# 📚 Personalized Study Guide Generator

##  Overview
The **Personalized Study Guide Generator** is an AI-driven web application that transforms raw study materials (notes, textbooks, past papers, etc.) into a structured, custom, multi-day study plan. It eliminates planning stress by analyzing your content and predicting high-priority exam topics and questions.

### 🎯 Key Features
* **Flexible Plan Modes:** Choose between a **Full Subject Exam** plan (using multiple module notes) or a **Single Module Focus** plan.
* **Custom Daily Schedule:** Generates a day-by-day study plan tailored to your specified number of study days.
* **Predictive Question Analysis:** Predicts high-probability **Short Answer Questions (SAQs)** and **Long Answer Questions (LAQs)** based on your content and past paper trends.
* **Integrated Answers (New!):** Provides comprehensive answers to all predicted SAQs and LAQs, generated directly from the uploaded study material context.
* **Key Term Mastery:** Instantly extracts and lists the most critical **Key Terms** you need to master.
* **Multi-Format Support:** Accepts input files in popular formats like `.pdf`, `.txt`, and images (`.png`, `.jpg`).

---

## 🛠️ Requirements & Setup

### Prerequisites
Before running the application, ensure you have the following installed:

1.  **Python 3.8+**
2.  **`pip`** (Python package installer)
3.  **Git** (for cloning the repository)

### Installation Steps

1.  **Clone the Repository:**
    Open your terminal or command prompt and clone the project:
    ```bash
    git clone [https://github.com/YourUsername/study-guide-generator.git](https://github.com/YourUsername/study-guide-generator.git)
    cd study-guide-generator
    ```

2.  **Create a Virtual Environment:**
    It is best practice to isolate project dependencies:
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    * **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    * **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install Dependencies:**
    Install all required packages listed in the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

---

## 🔑 Configuration (Gemini API Key)

This project uses the **Google Gemini API** for content analysis and generation.

1.  **Get Your API Key:** Obtain your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  **Create `.env` File:** In the **root directory** of the project, create a new file named `.env`.
3.  **Add Your Key:** Paste your API key into the file using the required variable name:

    ```env
    # .env file content
    GEMINI_API_KEY="YOUR_SECRET_API_KEY_GOES_HERE" 
    ```
    ***Note: The `.env` file is intentionally ignored by Git to protect your secret key.***

---

## ▶️ How to Run the Application

Once setup and configuration are complete:

1.  **Start the Server:**
    Run the main Python application file (assuming it's named `app.py` or similar):
    ```bash
    python app.py
    ```
2.  **Access the Web App:**
    The server will typically start on port 5000 (if using Flask) or a similar port. Open your web browser and navigate to:
    ```
    [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
    ```
3.  **Generate a Guide:**
    * **Select Plan Scope:** Choose between **"Full Subject Exam"** (requires uploading all module notes) or **"Single Module Focus"** (requires the module number and relevant notes).
    * Enter your desired number of study days (1-10).
    * Upload your primary **Study Notes/Book** file(s) and (Optional) **Past Papers**.
    * Click **"Generate Study Guide."**
---

## Interface

<img width="1806" height="914" alt="Screenshot 2025-12-06 113840" src="https://github.com/user-attachments/assets/4c243940-1352-4aee-b74b-8bb39dbaaf94" />

<img width="1831" height="912" alt="Screenshot 2025-12-06 113907" src="https://github.com/user-attachments/assets/f0aa18bc-bab0-42ad-b305-695694e5eafb" />

<img width="1824" height="915" alt="Screenshot 2025-12-06 113921" src="https://github.com/user-attachments/assets/f6a2daa3-6431-4da1-98d2-00c71b9628e4" />

<img width="1832" height="909" alt="Screenshot 2025-10-24 174801" src="https://github.com/user-attachments/assets/3bd648f6-c4c1-43cf-babf-fe2382b42e30" />

<img width="1920" height="1080" alt="Screenshot 2025-10-25 212913" src="https://github.com/user-attachments/assets/577d112c-d47f-4895-b908-36e918c36bd9" />

<img width="1920" height="1080" alt="Screenshot 2025-10-25 213058" src="https://github.com/user-attachments/assets/a7f4f6b0-41af-4303-b61e-f68219a9d707" />

<img width="1920" height="1080" alt="Screenshot 2025-10-25 213107" src="https://github.com/user-attachments/assets/fb157553-fa88-4064-b17b-a399a1bef520" />

<img width="1920" height="1080" alt="Screenshot 2025-10-25 213119" src="https://github.com/user-attachments/assets/892db613-2341-41e0-915b-fe5a39678b95" />

<img width="1920" height="1080" alt="Screenshot 2025-10-25 213131" src="https://github.com/user-attachments/assets/412ea411-88cb-4611-bb27-df9aad539ad3" />

<img width="1920" height="1080" alt="Screenshot 2025-10-25 213138" src="https://github.com/user-attachments/assets/43a8887c-deb1-4521-b1f5-68ff440a6e62" />



## 👤 Contact

Project Link: https://github.com/FelvinJoseph/Personalized-Study-Guide-Generator

Your Name: Felvin Joseph A F

Your Email: josephfelvin9@gmail.com
