# 🗄️ Dataset Instructions

Due to GitHub's file size limits, the 2GB+ SQLite database (`yelp.db`) used in this project cannot be hosted directly in this repository. 

To run this dashboard locally, please follow these steps:

1. **Download the raw data:** Visit the official [Yelp Open Dataset page](https://www.yelp.com/dataset).
2. **Format the data:** The original data is provided in JSON format. For this project, the JSON files were converted into a relational SQLite database. *(Note: You can use tools like `sqlite3` or Python scripts to convert the JSON to SQL).*
3. **Name the file:** Ensure your database file is named exactly `yelp.db`.
4. **Placement:** Place the `yelp.db` file directly into the root directory of this project (in the same folder as `app.py`).

Once the database is in place, you can run the application using `streamlit run app.py`.
