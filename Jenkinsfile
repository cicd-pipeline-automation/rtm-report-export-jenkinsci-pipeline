/************************************************************************************
 * 📘 RTM Report Export & Publishing Pipeline (Production-Ready)
 * ----------------------------------------------------------------------------------
 * Fetches Jira RTM data via REST API, generates HTML/PDF reports,
 * publishes to Confluence, and emails stakeholders.
 *
 * ✅ Headless (no Selenium/browser needed)
 * ✅ Works on Windows and Linux Jenkins agents
 * ✅ Uses modular Python scripts with isolated virtual environment
 * ✅ Secure credentials via Jenkins Credentials Store
 * ✅ UTF-8 safe for Windows console
 *
 * Author: DevOpsUser8413
 * Version: 1.1.0
 ************************************************************************************/

pipeline {
    agent any

    /***************************************************************
     * 🧭 Pipeline Options
     ***************************************************************/
    options {
        timestamps()                   // Include timestamps in console logs
        ansiColor('xterm')             // Enable colored output
        disableConcurrentBuilds()      // Prevent parallel executions
        buildDiscarder(logRotator(numToKeepStr: '15')) // keep last 15 builds
    }

    /***************************************************************
     * 🌍 Global Environment Variables
     ***************************************************************/
    environment {
        // 🧩 Jira Credentials
        JIRA_BASE   = credentials('jira-base')
        JIRA_USER   = credentials('jira-user')
        JIRA_TOKEN  = credentials('jira-token')

        // 🧩 Confluence Credentials
        CONFLUENCE_BASE   = credentials('confluence-base')
        CONFLUENCE_USER   = credentials('confluence-user')
        CONFLUENCE_TOKEN  = credentials('confluence-token')
        CONFLUENCE_SPACE  = 'DEMO'
        CONFLUENCE_TITLE  = 'RTM Test Execution Report'

        // 🧩 SMTP Email Credentials
        SMTP_HOST    = credentials('smtp-host')
        SMTP_PORT    = '587'
        SMTP_USER    = credentials('smtp-user')
        SMTP_PASS    = credentials('smtp-pass')
        REPORT_FROM  = credentials('sender-email')
        REPORT_TO    = credentials('multi-receivers')

        // 🧩 Project Metadata
        RTM_PROJECT     = 'RTM-DEMO'
        TEST_EXECUTION  = 'RD-4'
        VENV_PATH       = '.venv'

        // 🧩 UTF-8 Safe Python Environment
        PYTHONIOENCODING = 'utf-8'
        PYTHONUTF8 = '1'
        PYTHONLEGACYWINDOWSSTDIO = '1'
    }

    /***************************************************************
     * 🧱 Pipeline Stages
     ***************************************************************/
    stages {

        /***********************
         * Stage 1: Checkout Source Code
         ***********************/
        stage('Checkout Source Code') {
            steps {
                echo "🔍 Checking out repository from GitHub..."
                checkout scm
            }
        }

        /***********************
         * Stage 2: Setup Python Environment
         ***********************/
        stage('Setup Python Environment') {
            steps {
                echo "📦 Setting up Python virtual environment..."
                bat """
                    if not exist %VENV_PATH% python -m venv %VENV_PATH%
                    %VENV_PATH%\\Scripts\\python -m pip install --upgrade pip
                    %VENV_PATH%\\Scripts\\pip install -r requirements.txt
                """
            }
        }

        /***********************
         * Stage 3: Fetch Jira RTM Data
         ***********************/
        stage('Fetch RTM Data from Jira') {
            steps {
                echo "📡 Fetching RTM Test Execution data from Jira REST API..."
                bat """
                    chcp 65001
                    %VENV_PATH%\\Scripts\\python scripts\\fetch_rtm_data.py
                """
            }
        }

        /***********************
         * Stage 4: Generate Report
         ***********************/
        stage('Generate HTML/PDF Report') {
            steps {
                echo "🧾 Generating RTM HTML and PDF reports..."
                bat """
                    chcp 65001
                    %VENV_PATH%\\Scripts\\python scripts\\generate_rtm_report.py
                """
            }
        }

        /***********************
         * Stage 5: Publish to Confluence
         ***********************/
        stage('Publish to Confluence') {
            steps {
                echo "🌐 Publishing RTM report to Confluence space..."
                bat """
                    chcp 65001
                    %VENV_PATH%\\Scripts\\python scripts\\confluence_publish.py
                """
            }
        }

        /***********************
         * Stage 6: Email Notification
         ***********************/
        stage('Send Email Notification') {
            steps {
                echo "📧 Sending RTM report via SMTP email..."
                bat """
                    chcp 65001
                    %VENV_PATH%\\Scripts\\python scripts\\send_email.py
                """
            }
        }
    }

    /***************************************************************
     * 📦 Post-Build Cleanup and Notifications
     ***************************************************************/
    post {
        always {
            echo "📘 Workspace: ${env.WORKSPACE}"
            echo "🧹 Cleaning up temporary files..."
            bat 'timeout /t 5' // Wait 5s to release file locks
            cleanWs()
        }
        success {
            echo "✅ RTM Report Pipeline executed successfully!"
        }
        failure {
            echo "❌ RTM Report Pipeline failed. Check Jenkins console logs and export.out."
        }
    }
}
