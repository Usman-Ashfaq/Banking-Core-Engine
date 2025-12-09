# Banking-Core-Engine
A simplified Core Banking System demonstrating essential banking operations with transaction control using SQL TCL commands (COMMIT, ROLLBACK, SAVEPOINT). Focuses on customer management, account operations, and transaction integrity for academic evaluation.
core-banking-system/
│
├── app.py                    # Main Flask application
├── run.py                    # Production runner with environment config
├── wsgi.py                   # WSGI entry point for deployment
├── requirements.txt          # Python dependencies
├── tcl.sql                   # SQL TCL demonstration scripts
│
├── corebank.db               # SQLite database (auto-generated)
├── .env                      # Environment variables (create if needed)
├── .gitignore               # Git ignore file
│
├── templates/               # HTML templates directory
│   ├── login.html
│   ├── register.html
│   ├── index.html
│   ├── customer.html
│   ├── account.html
│   ├── transactions.html
│   └── audit.html
│
├── static/                  # Static files (CSS, JS, images)
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── database/                # Database-related files
│   ├── schema.sql          # Complete database schema
│   ├── sample_data.sql     # Sample data for testing
│   └── tcl_demo.sql        # Your existing tcl.sql moved here
│
├── tests/                   # Test files
│   ├── test_app.py         # Unit tests
│   ├── test_transactions.py
│   └── test_data/
│
└── documentation/          # Project documentation
    ├── ERD.pdf             # Entity Relationship Diagram
    ├── report.pdf          # Final project report
    ├── presentation.pptx   # Project defense slides
    └── screenshots/        # Application screenshots
