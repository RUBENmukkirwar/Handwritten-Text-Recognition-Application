import cv2
import numpy as np
from tkinter import *
from tkinter import filedialog, messagebox, ttk
import fpdf
from PIL import Image
import pytesseract
from difflib import SequenceMatcher
import os
import stat
from datetime import datetime

def check_file_access(filename):
    """
    Check if the file exists, is readable, and is a regular file.
    """
    # Check if file exists
    if not os.path.exists(filename):
        print("File does not exist.")
        return False

    # Check if the file can be read
    if not os.access(filename, os.R_OK):
        print("File is not readable. Permission denied.")
        return False

    # Get the file permissions
    file_stat = os.stat(filename)
    print(f"File permissions: {oct(file_stat.st_mode)}")

    # Check if the file is a regular file
    if not stat.S_ISREG(file_stat.st_mode):
        print("File is not a regular file.")
        return False

    print("File is accessible and ready for processing.")
    return True

class OCRProcessor:
    def __init__(self, tesseract_path):
        """
        Initialize the OCR Processor with the path to the Tesseract executable.
        """
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def process_image(self, filename):
        """
        Process the image and return the extracted text.
        """
        try:
            # Check file access
            if not check_file_access(filename):
                raise RuntimeError("File is not accessible.")

            # Read image with OpenCV
            img = cv2.imread(filename)
            if img is None:
                raise RuntimeError("Failed to read image. The file may be inaccessible or corrupted.")

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply dilation and erosion to remove some noise
            kernel = np.ones((1, 1), np.uint8)
            img_dilated = cv2.dilate(gray, kernel, iterations=1)
            img_eroded = cv2.erode(img_dilated, kernel, iterations=1)

            # Apply threshold to get a binary image
            _, img_thresh = cv2.threshold(img_eroded, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Recognize text with Tesseract
            text = pytesseract.image_to_string(img_thresh)
            return text
        except Exception as e:
            raise RuntimeError(f"Failed to process image: {e}")

    def save_to_pdf(self, text, output_dir="output"):
        """
        Save the extracted text to a PDF file.
        """
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = os.path.join(output_dir, f"converted_{timestamp}.pdf")

            pdf = fpdf.FPDF(format='letter')
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.write(5, text)
            pdf.output(pdf_filename)
            return pdf_filename
        except Exception as e:
            raise RuntimeError(f"Failed to save PDF: {e}")

    @staticmethod
    def calculate_similarity(text1, text2):
        """
        Calculate the similarity between two texts.
        """
        return SequenceMatcher(None, text1, text2).ratio() * 100

class OCRApp:
    def __init__(self, window, ocr_processor):
        self.window = window
        self.ocr_processor = ocr_processor
        self.window.title('Handwritten Text Recognition')
        self.window.geometry("700x350")
        self.window.config(background="white")

        self.result = ""

        self.create_widgets()

    def create_widgets(self):
        Label(self.window, text="Handwritten Text Recognition Using Pytesseract", width=80, height=2,
              font=("Arial", 12, "bold"), fg="black", bg='lightgrey').place(x=370, y=18, anchor='center')

        self.label_file_explorer = Label(self.window, text="See the Output Here", font=("Arial", 10, "bold"),
                                         width=90, height=12, fg="blue", bg="white")
        self.label_file_explorer.place(x=0, y=35)

        Button(self.window, text="Browse Files", fg="white", bg="black", font=("Arial", 10, "bold"), width=10,
               command=self.browse_files).place(x=250, y=270)

        Label(self.window, text="(Select an image)", bg="white", fg="black", font=("Arial", 8, "bold")).place(x=242, y=300)

        Button(self.window, text="Convert text to PDF", fg="white", bg="black", font=("Arial", 10, "bold"), width=15,
               command=self.convert_to_pdf).place(x=370, y=270)

        self.progress = ttk.Progressbar(self.window, orient=HORIZONTAL, length=300, mode='indeterminate')
        self.progress.place(x=200, y=320)

    def browse_files(self):
        filetypes = [("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(initialdir=r"C:\Users\dcrub\OneDrive\Desktop\code\New folder", title="Select a File", filetypes=filetypes)

        if not filename:
            return

        self.progress.start()

        try:
            # Process the image and get text
            self.result = self.ocr_processor.process_image(filename)

            # Update the label with the recognized text
            self.label_file_explorer.configure(text=self.result)

            # Calculate and display similarity (Optional)
            sample_text = "We start With good\n\nBecause all businesses should\n\nbe doing something good"
            accuracy = self.ocr_processor.calculate_similarity(sample_text, self.result)
            messagebox.showinfo("Accuracy", f"The accuracy of the model is {accuracy:.2f}%")
        except RuntimeError as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.progress.stop()

    def convert_to_pdf(self):
        if not self.result:
            messagebox.showwarning("No text", "No text found to convert to PDF!")
            return

        try:
            pdf_filename = self.ocr_processor.save_to_pdf(self.result)
            messagebox.showinfo("Success", f"Text successfully converted to PDF!\nSaved as {pdf_filename}")
        except RuntimeError as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    # Define the path to Tesseract (make sure this is correct)
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    root = Tk()
    ocr_processor = OCRProcessor(TESSERACT_PATH)
    app = OCRApp(root, ocr_processor)
    root.mainloop()
