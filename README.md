
### SETUP

```bash
# macos
virtualenv venv -p python3
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

```bash
# windows
python -m venv venv
venv/Scripts/activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### Run the Script
```bash
streamlit run 1_Sentiment_Analysis.py
```

### Building the Exe
```bash
pyinstaller --name=Dishoom --onefile --windowed --icon=icon.ico setup_for_packaging.py
```

## DESCRIPTION
---

The goal of this project is to drastically reduce the amount of time needed to examine hundreads of reviews from different source.
There was a long process of gathering and cleaning data that is now done automatically by the application.

I have connected a AI to the application that is going to help us doing some analysis on the sentiment of each review. 
- At the moment we are using the open-source HuggingFace to perform this operation.
- Each review is been classified as: `POSITIVE`, `NEGATIVE` or `neutral`

In this way we are going to have a overall view of the sentiment reviews for all the time period that is been taken in consideration.

This system is based on the assumption that there are different section that the business need to focus on.
In this case the sections are: `Product`, `Service`, `Ambience`

The logic behind this division is based on the `keywords`:
- We have a list of keywords for each section, if the keyword is find in the review, that review will be assigned to the appropriate section.

PS.
Eventually it will be possible to just create a dashboard based on this workflow:
- choose section names and keywords for each section


