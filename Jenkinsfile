/************************************************************************************
 * 📘 RTM Report Export & Publishing Pipeline
 * ----------------------------------------------------------------------------------
 * 1️⃣ Fetch RTM V2 Test Execution data via REST API
 * 2️⃣ Generate HTML + PDF report
 * 3️⃣ Publish report content to Confluence
 * 4️⃣ Email report to multiple recipients
 *
 * ✅ Fully headless (no Selenium or browser required)
 * ✅ Works in Windows or Linux Jenkins agents
 * ✅ Parameterized for remote trigger (Jira/RTM → Jenkins)
 * ✅ Modular Python-based scripts with virtual environment
 *
 * Author : DevOpsUser8413
 * Version: 2.0.0 (RTM V2 API)
 ************************************************************************************/

pipeline {
    agent any

    /***************************************************************
     * 🧭 Job Parameters (Enable Remote Trigger)
     ***************************************************************/
    parameters {
        string(
            name: 'RTM_PROJECT',
            defaultValue: 'RTM-DEMO',
            description: 'RTM/Jira Project Key (e.g. RTM-DEMO)'
        )
        string(
            name: 'TEST_EXECUTION',
            defaultValue: 'RD-4',
            description: 'RTM Test Execution Key (e.g. RD-4)'
        )
        string(
            name: 'EMAIL_TO',
            defaultValue: 'qa-team@example.com,dev-lead@example.com',
            description: 'Comma or semicolon separated list of recipients'
        )
        string(
            name: 'token',
            defaultValue: 'rtm-trigger-token',
            description: 'Shared secret/token when triggering this job remotely'
        )
    }

    /***************************************************************
     * 🌍 Global Environment
     ***************************************************************/
    environment {
        // 🔐 RTM / Jira API
        // These should be Jenkins "Secret Text" or "Username with password" credentials
        // Adjust IDs to match your Jenkins credentials store
        RTM_BASE_URL     = credentials('rtm-base-url')   // e.g. https://rtm.vendor.com
        RTM_USER         = credentials('rtm-user')        // RTM/Jira username or email
        RTM_TOKEN        = credentials('rtm-api-token')   // RTM/Jira API token

        // 🔹 Derived from parameters
        RTM_PROJECT_KEY  = "${params.RTM_PROJECT}"
        RTM_EXECUTION_KEY= "${params.TEST_EXECUTION}"

        // 🔹 Paths for generated artifacts
        RTM_OUTPUT_JSON  = "data/rtm_execution.json"
        RTM_REPORT_HTML  = "report/rtm_execution.html"
        RTM_REPORT_PDF   = "report/rtm_execution.pdf"

        // 🔹 Confluence API
        CONFLUENCE_BASE_URL = credentials('confluence-base')
        CONFLUENCE_USER     = credentials('confluence-user')
        CONFLUENCE_TOKEN    = credentials('confluence-token')
        CONFLUENCE_SPACE    = 'DEMO'
        CONFLUENCE_TITLE    = 'RTM Test Execution Report'
        // Optional: parent page id in Confluence
        CONFLUENCE_PARENT_ID = ''

        // 🔹 SMTP Email
        SMTP_HOST      = credentials('smtp-host')
        SMTP_PORT      = '587'
        SMTP_USER      = credentials('smtp-user')
        SMTP_PASSWORD  = credentials('smtp-password')
        EMAIL_FROM     = credentials('smtp-from')
        EMAIL_TO       = "${params.EMAIL_TO}"   // multiple receivers supported

        // 🔹 Misc
        PYTHON_VENV    = ".venv"
        RTM_VERIFY_SSL = "true"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
        timestamps()
    }

    stages {

        /***********************************************************
         * 🔒 Pre-check: Remote Token Validation (optional)
         ***********************************************************/
        stage('Validate Trigger Token') {
            when {
                expression { return params.token?.trim() }
            }
            steps {
                script {
                    // Replace with your real validation if needed
                    echo "Trigger token received: ${params.token}"
                    // Example hard check (optional):
                    // if (params.token.trim() != 'rtm-trigger-token') {
                    //     error "Invalid trigger token"
                    // }
                }
            }
        }

        /***********************************************************
         * 📦 Checkout Source
         ***********************************************************/
        stage('Checkout SCM') {
            steps {
                checkout scm
            }
        }

        /***********************************************************
         * 🐍 Setup Python Virtual Environment
         ***********************************************************/
        stage('Setup Python Env') {
            steps {
                script {
                    if (isUnix()) {
                        sh """
                            python3 -m venv ${PYTHON_VENV}
                            . ${PYTHON_VENV}/bin/activate
                            pip install --upgrade pip
                            pip install -r requirements.txt
                        """
                    } else {
                        bat """
                            python -m venv %PYTHON_VENV%
                            call %PYTHON_VENV%\\Scripts\\activate
                            pip install --upgrade pip
                            pip install -r requirements.txt
                        """
                    }
                }
            }
        }

        /***********************************************************
         * 📥 Fetch RTM V2 Test Execution Data
         ***********************************************************/
        stage('Fetch RTM Data (V2 API)') {
            steps {
                script {
                    if (isUnix()) {
                        sh """
                            . ${PYTHON_VENV}/bin/activate
                            mkdir -p data
                            python scripts/fetch_rtm_data.py
                        """
                    } else {
                        bat """
                            call %PYTHON_VENV%\\Scripts\\activate
                            if not exist data mkdir data
                            python scripts\\fetch_rtm_data.py
                        """
                    }
                }
            }
        }

        /***********************************************************
         * 📄 Generate HTML + PDF Report
         ***********************************************************/
        stage('Generate RTM Report') {
            steps {
                script {
                    if (isUnix()) {
                        sh """
                            . ${PYTHON_VENV}/bin/activate
                            mkdir -p report
                            python scripts/generate_rtm_report.py
                        """
                    } else {
                        bat """
                            call %PYTHON_VENV%\\Scripts\\activate
                            if not exist report mkdir report
                            python scripts\\generate_rtm_report.py
                        """
                    }
                }
            }
        }

        /***********************************************************
         * 📰 Publish to Confluence
         ***********************************************************/
        stage('Publish to Confluence') {
            steps {
                script {
                    if (isUnix()) {
                        sh """
                            . ${PYTHON_VENV}/bin/activate
                            python scripts/confluence_publish.py
                        """
                    } else {
                        bat """
                            call %PYTHON_VENV%\\Scripts\\activate
                            python scripts\\confluence_publish.py
                        """
                    }
                }
            }
        }

        /***********************************************************
         * ✉ Email Notification (multiple receivers)
         ***********************************************************/
        stage('Send Email Notification') {
            steps {
                script {
                    if (isUnix()) {
                        sh """
                            . ${PYTHON_VENV}/bin/activate
                            python scripts/send_email.py
                        """
                    } else {
                        bat """
                            call %PYTHON_VENV%\\Scripts\\activate
                            python scripts\\send_email.py
                        """
                    }
                }
            }
        }
    }

    /***************************************************************
     * 📌 Post Actions
     ***************************************************************/
    post {
        always {
            archiveArtifacts artifacts: 'report/*,data/*', fingerprint: true
        }
        success {
            echo "✅ RTM report generation pipeline completed successfully."
        }
        failure {
            echo "❌ RTM report generation pipeline failed. Check logs for details."
        }
    }
}
