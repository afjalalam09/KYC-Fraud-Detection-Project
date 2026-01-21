# AI-Powered Identity Verification & Fraud Detection System 🕵️‍♂️✅

## 📌 Project Overview
This project is an **AI-based KYC (Know Your Customer) automation system**. It helps organizations verify user identities instantly by extracting details from ID cards (like Pan Card/Aadhar) and matching the user's live face with the ID photo to detect fraud.

Unlike manual verification, which is slow and error-prone, this system uses **OCR (Optical Character Recognition)** and **Computer Vision** to provide results in seconds.

## 🚀 Key Features
* **📄 Automated OCR:** Extracts Name, DOB, and ID Number from uploaded ID cards using **Tesseract OCR**.
* **👤 Face Matching AI:** Compares the uploaded ID photo with a live uploaded selfie to check for identity mismatch.
* **🛢️ Secure Database:** Stores verified user data securely in a **MySQL Database**.
* **📊 Admin Dashboard:** A clean interface to view user details and verification status.
* **🔒 Fraud Detection:** Automatically flags mismatches or unclear documents.

## 🛠️ Technology Stack
* **Backend:** Python, Flask
* **Database:** MySQL
* **AI/ML:** OpenCV, Pytesseract (OCR), NumPy
* **Frontend:** HTML, CSS
* **Tools:** VS Code, Git/GitHub, Postman

## ⚙️ Installation & Setup

### 1. Prerequisites
* Python (3.x) installed.
* MySQL Server installed.
* **Tesseract OCR** installed on your system.
    * *Windows users must add Tesseract path to Environment Variables.*

### 2. Clone the Repository
```bash
git clone [https://github.com/afjalalam09/KYC-Fraud-Detection-Project.git](https://github.com/afjalalam09/KYC-Fraud-Detection-Project.git)
cd KYC-Fraud-Detection-Project
