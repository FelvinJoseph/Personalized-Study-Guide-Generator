import os
import fitz # PyMuPDF for PDF to Image conversion
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv 
from google import genai
from google.genai import types
from google.genai.errors import APIError
from PIL import Image 
import PyPDF2 
# This import is CRITICAL for structured output validation
from schemas import StudyGuide 

# --- 1. CONFIGURATION & INITIALIZATION ---
load_dotenv() 

app = Flask(__name__) 
# Ensure the 'uploads' directory exists or Flask will error when saving files
app.config['UPLOAD_FOLDER'] = 'uploads/' 
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}

try:
    # Initialize the Gemini client
    client = genai.Client()
    print("Gemini Client initialized successfully.")
except Exception as e:
    print(f"Error initializing Gemini Client: {e}")

# --- 2. HELPER FUNCTIONS ---

def allowed_file(filename):
    """Checks if a file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file using PyPDF2 (for text-based PDFs)."""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
    except Exception as e:
        # Return None if PyPDF2 fails (likely an image-based PDF)
        return None 
    return text.strip()

def extract_content_parts(file_path, filename, temp_paths_list):
    """
    Extracts content from a file. If PDF text extraction fails, 
    it converts pages to images for Gemini's OCR capability.
    """
    file_ext = filename.rsplit('.', 1)[1].lower()
    content_parts = []
    
    if file_ext == 'pdf':
        text = extract_text_from_pdf(file_path)
        
        if text and len(text) > 10: 
            # Use text if extraction was successful
            content_parts.append(types.Part(text=text))
        else:
            # Fallback: Convert pages to images for scanned PDFs
            try:
                doc = fitz.open(file_path)
                for i, page in enumerate(doc):
                    # Set resolution for high quality image extraction
                    mat = fitz.Matrix(2.0, 2.0) 
                    pix = page.get_pixmap(matrix=mat)
                    
                    img_output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_page_{i}_{os.path.basename(file_path)}.png")
                    pix.save(img_output_path)
                    temp_paths_list.append(img_output_path) 
                    
                    img = Image.open(img_output_path)
                    content_parts.append(img)
                
                doc.close()
                if not content_parts:
                    return None, "Error: PDF is either empty or corrupted."
            except Exception as e:
                print(f"PyMuPDF Conversion Error: {e}")
                return None, "Error: Failed to process PDF. It may be corrupt or encrypted."
            
    elif file_ext in ['png', 'jpg', 'jpeg']:
        img = Image.open(file_path)
        content_parts.append(img)
        
    elif file_ext == 'txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        content_parts.append(types.Part(text=text))
        
    else:
        return None, f"Error: Unsupported file type: {file_ext}"
        
    return content_parts, None


# --- GENERATOR FUNCTION (Handles AI call) ---
def generate_study_guide(content_parts, study_days, module_number): 
    """
    Calls the Gemini API to generate a structured study guide, filtering by module if specified.
    """
    system_instruction = (
        "You are an expert personalized study planner. Analyze the provided "
        "study material, along with the user's total study days, and strictly output a "
        "day-by-day study plan in the required JSON format. The total_days field MUST match "
        "the number of DayPlan objects in the study_plan list. Ensure the tasks are highly actionable."
    )
    
    # Conditionally add module filtering to the prompt
    module_filter = ""
    if module_number:
        module_filter = f"and strictly focus the plan, terms, and questions on the topic/content related to **{module_number}**."


    text_prompt = (
        f"Analyze the uploaded document content and any previous exam papers provided. "
        f"Generate a complete, personalized study plan based on this material for exactly **{study_days} days** {module_filter}. "
        "Also, extract 5-7 essential key terms. "
        "Generate **2-3 high-priority practice exercises/questions** derived from analyzing common or highly-weighted topics in previous exam papers. "
        "Finally, predict and list **8 short answer questions (SAQs)** and **4 long answer questions (LAQs)** based on the entire study material. "
        "Ensure the structure strictly adheres to the required JSON schema, including the lists for short_answer_questions and long_answer_questions."
        "If a module number was specified, ensure all generated content (schedule, terms, questions) strictly aligns with that module."
    )

    full_contents = [types.Part(text=text_prompt)] + content_parts 
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=full_contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=StudyGuide,
                temperature=0.2
            )
        )
        # Validate and return the structured Pydantic object
        return StudyGuide.model_validate_json(response.text)
        
    except APIError as e:
        print(f"Gemini API Error: {e}")
        return f"Gemini API Error: {e}"
    except Exception as e:
        print(f"Generation or Validation Error: {e}")
        return f"Generation or Validation Error: {e}"


# --- 3. FLASK ROUTES ---

@app.route('/')
def index():
    # Ensure the uploads directory exists before rendering the page
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if 'file' not in request.files:
        return jsonify({'error': 'No study notes file uploaded.'}), 400
    
    file = request.files['file']
    
    # 1. Input Validation and Parsing
    try:
        study_days = int(request.form.get('study_days', 3)) 
        if not 1 <= study_days <= 10: 
             return jsonify({'error': 'Study days must be between 1 and 10.'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid number of study days provided.'}), 400

    # Retrieve the optional module number field
    module_number = request.form.get('module_number', '').strip() 

    # 2. File Validation and Setup
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'No selected file or invalid file type for study notes.'}), 400

    all_content_parts = []
    temp_file_paths = [] 

    # --- Process Main Study File ---
    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path) 
    temp_file_paths.append(file_path) 
    
    content_parts, error = extract_content_parts(file_path, filename, temp_file_paths) 
    
    if error:
        return jsonify({'error': error}), 500
    
    all_content_parts.extend(content_parts)

    # --- Process Multiple Optional Past Papers ---
    past_papers_list = request.files.getlist('past_paper')
    
    for i, past_paper_file in enumerate(past_papers_list):
        
        if not past_paper_file or not past_paper_file.filename:
            continue
        
        paper_name = f'past_{i}_{past_paper_file.filename}'
        past_paper_path = os.path.join(app.config['UPLOAD_FOLDER'], paper_name)
        past_paper_file.save(past_paper_path)
        temp_file_paths.append(past_paper_path) 
        
        paper_ext = paper_name.rsplit('.', 1)[1].lower()
        paper_text = None

        # Extract text from past papers 
        if paper_ext == 'pdf':
            paper_text = extract_text_from_pdf(past_paper_path)
            if not paper_text:
                 # If text extraction fails on a past paper PDF, treat it as empty or unreadable
                 paper_text = f"WARNING: Could not read content from past paper #{i+1}. Treating as empty."

        elif paper_ext == 'txt':
            with open(past_paper_path, 'r', encoding='utf-8') as f:
                paper_text = f.read()

        if paper_text:
            all_content_parts.append(
                types.Part(text=f"\n\n--- PREVIOUS EXAM PAPER #{i+1} FOR ANALYSIS ---\n\n" + paper_text)
            )

    # --- AI Generation ---
    try:
        study_guide_obj = generate_study_guide(all_content_parts, study_days, module_number) 

        if isinstance(study_guide_obj, str): 
            return jsonify({'error': f'AI Generation Failed: {study_guide_obj}'}), 500
        
        return jsonify({
            'success': True, 
            'study_guide': study_guide_obj.model_dump()
        }), 200

    except Exception as e:
        print(f"Processing Error: {e}")
        return jsonify({'error': f'An unexpected error occurred during processing: {e}'}), 500

    finally:
        # Clean up ALL temporary files
        for path in temp_file_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as e:
                    print(f"Error deleting file {path}: {e}")


# --- 4. MAIN EXECUTION BLOCK ---
if __name__ == '__main__':
    # Ensure the uploads directory exists before starting the app
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
