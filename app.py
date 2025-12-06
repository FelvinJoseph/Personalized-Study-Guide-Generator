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
from schemas import StudyGuide, QuestionAnswer # Updated import

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

def extract_content_parts(file_path, filename, temp_paths_list, is_main_notes=True):
    """
    Extracts content from a single file. If PDF text extraction fails, 
    it converts pages to images for Gemini's OCR capability (only for the main notes).
    """
    file_ext = filename.rsplit('.', 1)[1].lower()
    content_parts = []
    
    if file_ext == 'pdf':
        text = extract_text_from_pdf(file_path)
        
        if text and len(text) > 10: 
            # Use text if extraction was successful
            content_parts.append(types.Part(text=text))
        elif is_main_notes: # Only use OCR fallback for the primary study material
            # Fallback: Convert pages to images for scanned PDFs
            try:
                doc = fitz.open(file_path)
                for i, page in enumerate(doc):
                    if i >= 20: # Limit OCR processing to the first 20 pages for context window management
                        print("WARNING: Stopping PDF-to-Image conversion at 20 pages.")
                        break 
                    
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
        else:
             # If it's a supplemental file (like a module or past paper) and text extraction failed,
             # we treat it as unreadable text rather than trying OCR.
             return None, f"Warning: Could not extract text from supplemental PDF: {filename}. Skipping."
            
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
def generate_study_guide(content_parts, study_days, plan_mode, module_number): 
    """
    Calls the Gemini API to generate a structured study guide, tailored for subject or module.
    """
    system_instruction = (
        "You are an expert personalized study planner. Analyze the provided "
        "study material, along with the user's total study days, and strictly output a "
        "day-by-day study plan in the required JSON format. The total_days field MUST match "
        "the number of DayPlan objects in the study_plan list. Ensure the tasks are highly actionable. "
        "Crucially, for every short and long answer question generated, you MUST provide a comprehensive answer "
        "in the 'answer' field of the QuestionAnswer object, directly based on the notes provided."
    )
    
    # Set the prompt based on the planning mode
    module_filter = ""
    if plan_mode == 'module' and module_number:
        module_filter = f"Focus the study plan and all generated questions/answers strictly on the content related to the module: **{module_number}**."
    elif plan_mode == 'subject':
        module_filter = "The provided files cover all modules for a full subject exam. Create a comprehensive, subject-level study plan covering all topics."
    else:
        module_filter = "Generate a standard study plan for the provided materials."


    text_prompt = (
        f"Analyze the uploaded document content and any previous exam papers provided. "
        f"Generate a complete, personalized study plan based on this material for exactly **{study_days} days**. "
        f"{module_filter} "
        "Also, extract 5-7 essential key terms. "
        "Generate **2-3 high-priority practice exercises/questions** derived from analyzing common or highly-weighted topics in previous exam papers. "
        "Finally, predict and list **8 short answer questions (SAQs)** and **4 long answer questions (LAQs)**. "
        "**For every question generated (SAQ and LAQ), you MUST also provide a complete answer based on the context provided in the notes/papers.**"
        "Ensure the structure strictly adheres to the required JSON schema."
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
    # 1. Input Validation and Parsing
    
    plan_mode = request.form.get('plan_mode', 'subject') # Default to subject mode

    if plan_mode == 'module':
        # In module mode, 'file' is the module notes
        if 'file' not in request.files:
            return jsonify({'error': 'No module study notes file uploaded.'}), 400
        module_notes_files = [request.files['file']]
        module_number = request.form.get('module_number', '').strip()
        if not module_number:
            return jsonify({'error': 'Module study plan selected, but no Module Number provided.'}), 400
    
    elif plan_mode == 'subject':
        # In subject mode, 'all_modules_file' contains potentially multiple files
        module_notes_files = request.files.getlist('all_modules_file')
        module_number = None # No specific module number needed
        if not module_notes_files or not any(f.filename for f in module_notes_files):
             return jsonify({'error': 'Subject study plan selected, but no module notes files uploaded.'}), 400

    else:
        return jsonify({'error': 'Invalid planning mode selected.'}), 400
        
    
    try:
        study_days = int(request.form.get('study_days', 3)) 
        if not 1 <= study_days <= 10: 
             return jsonify({'error': 'Study days must be between 1 and 10.'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid number of study days provided.'}), 400

    
    all_content_parts = []
    temp_file_paths = [] 
    
    # --- Process Study Files (Main Notes / All Modules) ---
    
    for i, file in enumerate(module_notes_files):
        if file.filename == '' or not allowed_file(file.filename):
            continue 
            
        is_main_notes = (plan_mode == 'module' and i == 0) # Only first file in module mode gets OCR fallback
        
        filename = file.filename
        # Prefix file names to distinguish multiple module files in the uploads folder
        file_prefix = 'module_notes' if plan_mode == 'subject' else 'main_notes'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{file_prefix}_{i}_{filename}')
        file.save(file_path) 
        temp_file_paths.append(file_path) 
        
        content_parts, error = extract_content_parts(file_path, filename, temp_file_paths, is_main_notes=is_main_notes) 
        
        # Handle errors from file extraction
        if error and "Error:" in error:
            return jsonify({'error': error}), 500
        
        if content_parts:
            # Add a separator to distinguish content from different files for the model
            file_identifier = f"\n\n--- STUDY MATERIAL FILE #{i+1} ({filename}) ---\n\n"
            all_content_parts.append(types.Part(text=file_identifier))
            all_content_parts.extend(content_parts)
            
    if not all_content_parts:
        return jsonify({'error': 'Failed to extract any readable content from the primary study materials.'}), 500


    # --- Process Multiple Optional Past Papers ---
    past_papers_list = request.files.getlist('past_paper')
    
    for i, past_paper_file in enumerate(past_papers_list):
        
        if not past_paper_file or not past_paper_file.filename or not allowed_file(past_paper_file.filename):
            continue
        
        paper_name = f'past_{i}_{past_paper_file.filename}'
        past_paper_path = os.path.join(app.config['UPLOAD_FOLDER'], paper_name)
        past_paper_file.save(past_paper_path)
        temp_file_paths.append(past_paper_path) 
        
        paper_ext = paper_name.rsplit('.', 1)[1].lower()
        paper_text = None

        # Extract text from past papers (no OCR fallback for supplemental files) 
        if paper_ext == 'pdf':
            paper_text = extract_text_from_pdf(past_paper_path)
            if not paper_text:
                paper_text = f"WARNING: Could not read content from past paper PDF #{i+1}. Treating as empty."

        elif paper_ext == 'txt':
            with open(past_paper_path, 'r', encoding='utf-8') as f:
                paper_text = f.read()

        if paper_text:
            all_content_parts.append(
                types.Part(text=f"\n\n--- PREVIOUS EXAM PAPER #{i+1} FOR ANALYSIS ---\n\n" + paper_text)
            )

    # --- AI Generation ---
    try:
        study_guide_obj = generate_study_guide(all_content_parts, study_days, plan_mode, module_number) 

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