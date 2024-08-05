
# Symptom_Sage



Symptom_Sage is an intuitive web application designed to detect pneumonia from chest X-rays, generate comprehensive reports pinpointing affected lung areas, and seamlessly connect doctors and patients. This application was awarded first place at the BIT INCEPTRA'24 Hackathon.

## Features

- **Pneumonia Detection**: Upload chest X-rays to detect pneumonia using advanced machine learning algorithms.
- **Detailed Reporting**: Generate reports indicating which parts of the lungs are affected.
- **Doctor-Patient Interaction**: Intuitive interface for doctors to add prescriptions, view X-rays, and provide diagnoses.
- **Secure & Private**: Ensures the privacy and security of patient data.

## Installation

To get started with Symptom_Sage, follow these steps:

### Prerequisites

- Python 3.10+
- Flask
- TensorFlow 
- MySQL (for database)

### Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/Pratz1337/Symptom_Sage.git
    cd Symptom_Sage
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up the database:
    ```bash
    # Ensure MongoDB is running
    mongod --config /usr/local/etc/mongod.conf
    ```

5. Start the Flask app:
    ```bash
    flask run
    ```

6. Open your browser and navigate to:
    ```
    http://127.0.0.1:5000
    ```

## Usage

1. **Upload X-Ray**: Upload the chest X-ray image.
2. **Detection**: The app processes the image to detect signs of pneumonia.
3. **Report Generation**: Receive a detailed report highlighting the affected lung areas.
4. **Doctor Interaction**: Connect with a doctor who can view the X-ray, add prescriptions, and give their diagnosis.

## Our Journey

### BIT INCEPTRA'24 Hackathon

Symptom_Sage emerged victorious at the BIT INCEPTRA'24 Hackathon. The competition was fierce, but our innovative approach to leveraging machine learning for medical diagnostics stood out. Our team's dedication and hard work were instrumental in this success.

### Challenges Overcome

- **Data Privacy**: Ensuring the confidentiality and security of patient data.
- **Accuracy**: Fine-tuning the model to achieve high accuracy in pneumonia detection.
- **User Interface**: Designing an intuitive interface for both patients and doctors.

## Future Enhancements

- **Integration with EHR Systems**: Seamless integration with electronic health records for better data management.
- **Real-Time Consultation**: Adding real-time video consultation features.
- **Mobile Application**: Developing a mobile app for easier access.

## Contributing

We welcome contributions from the community! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.



