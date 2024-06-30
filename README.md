Here's the README in Markdown format:

```markdown
# Hever Scraper

Hever Scraper is a data scraping tool written in Python, designed to gather and maintain the data used by the [Hever Index](https://github.com/ShahafShavit/hever-index) project. This scraper collects relevant data and stores it in a `.db` database file, which is utilized by the Hever Index website.

## Table of Contents

- [Description](#description)
- [Installation and Setup](#installation-and-setup)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact Information](#contact-information)

## Description

Hever Scraper is responsible for extracting data from mcc public stores webpage. This data is then processed and stored in a structured database format (.db), which is used by the Hever Index project to provide accurate and up-to-date information.

## Installation and Setup

To get started with Hever Scraper, follow these steps:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ShahafShavit/hever-scraper.git
   cd hever-scraper
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**  
   Create a `.env` file in the root directory and add the necessary environment variables as shown in the `.env.example` file.

## Usage

To run the scraper and update the database file, use the following command:

```bash
python scraper.py
```

This command will start the scraping process, collecting data from the specified sources and updating the `.db` file.

## Contributing

We welcome contributions! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact Information

For any inquiries, please contact Shahaf Shavit at [shavitshahaf@gmail.com].
```

You can copy and paste this Markdown text into your README.md file in the `hever-scraper` repository. Let me know if you need any further modifications!
