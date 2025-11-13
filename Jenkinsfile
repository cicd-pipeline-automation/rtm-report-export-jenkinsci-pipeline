/************************************************************************************
 * 📘 RTM Report Export & Publishing Pipeline
 * ----------------------------------------------------------------------------------
 * Fetches Jira RTM data via REST API, generates HTML/PDF report,
 * publishes to Confluence, and emails stakeholders.
 *
 * ✅ Fully headless (no Selenium or browser required)
 * ✅ Works in Windows or Linux Jenkins agents
 * ✅ Parameterized for remote trigger (Jira → Jenkins)
 * ✅ Modular Python-based scripts with virtual environment
 *
 * Author : DevOpsUser8413
 * Version: 1.1.0
 ************************************************************************************/

pipeline {
    agent any

    /***************************************************************
     * 🧭 Job Parameters (Enable Remote Trigger)
     ***************************************************************/
    parameters {
        string(name: 'RTM_PROJECT', defaultValue: 'RTM-DEMO', description: 'Jira RTM Project Key')
        string(name: 'TEST_EXECUTION', defaultValue: 'RD-4', description: 'Jira RTM Test Execution Key')
        string(name: 'token', defaultValue: 'rtm-trigger-token', description: 'Webhook trigger token for remote builds')
    }

    /***************************************************************
     * 🧰 Global Options
     ***************************************************************/
    options {
        timestamps()          // Show build timestamps
        ansiColor('xterm')    // Colored console output
        disableConcurrentBuilds()
    }

    /***************************************************************
     * 🌍 Environment Variables
     ***************************************************************/
    environment {
        // 🔹 Jira API
        JIRA_BASE   = credentials('jira-base')
        JIRA_USER   = credentials('jira-user')
        JIRA_TOKEN  = credentials('jira-token')
        JIRA_PROJECT_KEY = "${params.RTM_PROJECT}"
        JIRA_EXECUTION_ID = "${params.TEST_EXECUTION}"

        // 🔹 Confluence API
        CONFLUENCE_BASE   = credentials('confluence-base')
        CONFLUENCE_USER   = credentials('confluence-user')
        CONFLUENCE_TOKEN  = credentials('confluence-token')
        CONFLUENCE_SPACE  = 'DEMO'
        CONFLUENCE_TITLE  = 'RTM Test Execution Report'

        // 🔹 SMTP Email
        SMTP_HOST    = credentials('smtp-host')
        SMTP_PORT    = '587'
        SMTP_USER    = credentials('smtp-user')
        SMTP_PASS    = credentials('smtp-pass')
        REPORT_FROM  = credentials('sender-email')
        REPORT_TO    = credentials('multi-receivers')

        // 🔹 Python virtual environment path
        VENV_PATH       = "C:\\Jenkins\\venvs\\rtm_rtm_pipeline"

        // 🔹 Encoding and runtime configuration
        PYTHONIOENCODING = 'utf-8'
        PYTHONUTF8 = '1'
        PYTHONLEGACYWINDOWSSTDIO = '1'
    }

    /***************************************************************
     * 🧱 Pipeline Stages
     ***************************************************************/
    stages {

        /***********************
         * Stage 1: Checkout
         ***********************/
        stage('Checkout Source Code') {
            steps {
                echo "🔍 Checking out repository from Git..."
                checkout scm
            }
        }

        /***********************
         * Stage 2: Setup Python Environment
         ***********************/
        stage('Setup Python Environment') {
            steps {
                echo "⚡ Optimizing Python venv setup (with caching)..."

                bat """
                    REM -------- Step 1: Create venv only once --------
                    if not exist %VENV_PATH% (
                        echo Creating Python virtual environment for FIRST time...
                        python -m venv %VENV_PATH%
                        echo Upgrading pip...
                        %VENV_PATH%\\Scripts\\python -m pip install --upgrade pip
                        echo Installing dependencies...
                        %VENV_PATH%\\Scripts\\pip install -r requirements.txt
                        echo Done.
                        goto END
                    )

                    REM -------- Step 2: Check if requirements.txt changed --------
                    if not exist .req.hash (
                        echo NEW HASH FILE - computing...
                        certutil -hashfile requirements.txt MD5 > .req.hash
                        goto END
                    )

                    certutil -hashfile requirements.txt MD5 > .req.new
                    fc .req.hash .req.new > nul
                    if errorlevel 1 (
                        echo Requirements changed! Reinstalling packages...
                        %VENV_PATH%\\Scripts\\pip install -r requirements.txt
                        move /Y .req.new .req.hash > nul
                    ) else (
                        echo Requirements unchanged — using cached venv. Fast!
                        del .req.new
                    )

                    :END
                """
            }
        }

        /***********************
         * Stage 3: Fetch Jira RTM Data
         ***********************/
        stage('Fetch RTM Data from Jira') {
            steps {
                echo "📡 Fetching RTM Test Execution data from Jira REST API..."
                script {
                    def result = bat(
                        script: """
                            echo Running Jira RTM Data Fetch...
                            %VENV_PATH%\\Scripts\\python scripts\\fetch_rtm_data.py
                        """,
                        returnStatus: true
                    )
                    if (result != 0) {
                        error("❌ Jira RTM data fetch failed. Check logs for details.")
                    }
                }
            }
        }

        /***********************
         * Stage 4: Generate HTML/PDF Report
         ***********************/
        stage('Generate HTML/PDF Report') {
           when { expression { fileExists('data/rtm_data.json') } }
            steps {
                echo "🧾 Generating RTM HTML and PDF reports..."
                bat """
                    echo Generating reports...
                    %VENV_PATH%\\Scripts\\python scripts\\generate_rtm_report.py
                """
            }
        }

        /***********************
         * Stage 5: Publish to Confluence
         ***********************/
        stage('Publish to Confluence') {
           //when { expression { fileExists('rtm_report.html') } }
            steps {
                echo "🌐 Publishing RTM report to Confluence space..."
                bat """
                    echo Uploading report to Confluence...
                    %VENV_PATH%\\Scripts\\python scripts\\confluence_publish.py
                """
            }
        }

        /***********************
         * Stage 6: Email Notification
         ***********************/
        stage('Send Email Notification') {
           //when { expression { fileExists('rtm_report.pdf') } }
            steps {
                echo "📧 Sending RTM report via email..."
                bat """
                    echo Sending email notification to stakeholders...
                    %VENV_PATH%\\Scripts\\python scripts\\send_email.py
                """
            }
        }
    }

    /***************************************************************
     * 📦 Post-Build Actions
     ***************************************************************/
    post {
        always {
            echo "📘 Jenkins workspace: ${env.WORKSPACE}"
            echo "🧹 Cleaning temporary files..."
        }
        success {
            echo "✅ RTM Report Export & Publishing Pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed. Check Jenkins console logs for detailed error output."
        }
    }
}
