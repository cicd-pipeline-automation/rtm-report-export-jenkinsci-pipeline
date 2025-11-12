// ======================================================================
// 🧩 Jenkins Pipeline: RTM Test Execution Report Automation
// ----------------------------------------------------------------------
// This pipeline automates the following workflow:
//   1️⃣ Exports RTM Test Execution Report (via Selenium headless browser)
//   2️⃣ Publishes exported report to Confluence space
//   3️⃣ Sends email notification with the report attached
// ----------------------------------------------------------------------
// Compatible with: Windows Jenkins Agent
// Prerequisites: Chrome + ChromeDriver + Python 3 installed on agent
// ======================================================================

pipeline {

  agent any
  options { 
    timestamps() 
    ansiColor('xterm')
  }

  // ---------------------------------------------------------------
  // 🔧 Pipeline Parameters
  // ---------------------------------------------------------------
  parameters {
    string(name: 'RTM_PROJECT',    defaultValue: 'RTM-DEMO', description: 'RTM Project Key')
    string(name: 'TEST_EXECUTION', defaultValue: 'RD-4',     description: 'RTM Test Execution Key')
    choice(name: 'REPORT_FORMAT',  choices: ['pdf'],         description: 'Export format (RTM Cloud supports PDF only)')
  }

  // ---------------------------------------------------------------
  // 🌍 Environment Configuration (Credentials from Jenkins)
  // ---------------------------------------------------------------
  environment {
    // --- Jira / RTM ---
    JIRA_BASE = credentials('jira-base')          // e.g. https://yourcompany.atlassian.net
    JIRA_USER = credentials('jira-user')
    JIRA_PASS = credentials('jira-token')

    // --- Confluence ---
    CONFLUENCE_BASE  = credentials('confluence-base')
    CONFLUENCE_USER  = credentials('confluence-user')
    CONFLUENCE_TOKEN = credentials('confluence-token')
    CONFLUENCE_SPACE = 'DEV'
    CONFLUENCE_TITLE = "Test Execution Report – ${RTM_PROJECT}/${TEST_EXECUTION}"

    // --- Email ---
    SMTP_HOST   = credentials('smtp-host')
    SMTP_PORT   = '587'
    SMTP_USER   = credentials('smtp-user')
    SMTP_PASS   = credentials('smtp-pass')
    REPORT_FROM = credentials('sender-email')
    REPORT_TO   = credentials('multi-receivers')  // Comma-separated recipients

    // --- Python UTF-8 support ---
    PYTHONIOENCODING = 'utf-8'
  }

  // ---------------------------------------------------------------
  // 🚦 Pipeline Stages
  // ---------------------------------------------------------------
  stages {

    // -------------------------------------------------------------
    // Stage 1: Checkout Repository
    // -------------------------------------------------------------
    stage('Checkout Source Code') {
      steps {
        echo "🔄 Checking out source code from Git repository..."
        checkout scm
      }
    }

    // -------------------------------------------------------------
    // Stage 2: Setup Python Virtual Environment
    // -------------------------------------------------------------
    stage('Setup Python Environment') {
      steps {
        echo "🐍 Setting up Python virtual environment..."
        bat """
          if not exist .venv python -m venv .venv
          .venv\\Scripts\\python -m pip install --upgrade pip
          .venv\\Scripts\\pip install selenium requests
        """
      }
    }

    stage('Validate Chrome') {
      steps {
        bat '''
          echo Verifying Chrome setup...
          where chrome.exe || (echo Chrome not found && exit /b 1)
          where chromedriver.exe || (echo ChromeDriver not found && exit /b 1)
        '''
      }
    }

    // -------------------------------------------------------------
    // Stage 3: Export RTM Report via Selenium
    // -------------------------------------------------------------
    stage('Export RTM Report (Selenium)') {
      steps {
        script {
          echo "🚀 Starting RTM report export for ${params.RTM_PROJECT}/${params.TEST_EXECUTION}..."

          // Run Selenium script
          bat """
            set DOWNLOAD_DIR=report
            .venv\\Scripts\\python scripts\\rtm_export_selenium.py > export.out 2>&1
          """

          // Parse export logs
          def output = readFile('export.out')
          echo output

          // Extract the downloaded PDF path
          def m = (output =~ /Found report: (.+\\.pdf)/)
          if (!m) {
            error "❌ Export failed — no PDF found in export.out logs!"
          }
          env.REPORT_FILE = m[0][1].trim()
          echo "✅ RTM report successfully downloaded: ${env.REPORT_FILE}"
        }
      }

      post {
        success {
          echo "📦 Archiving generated RTM PDF report..."
          archiveArtifacts artifacts: 'report/**/*.pdf', fingerprint: true
        }
        failure {
          echo "⚠️ RTM export stage failed — check export.out for errors."
        }
      }
    }

    // -------------------------------------------------------------
    // Stage 4: Publish Report to Confluence
    // -------------------------------------------------------------
    stage('Publish to Confluence') {
      steps {
        script {
          echo "📤 Publishing RTM report to Confluence..."

          def title = "RTM Test Execution Report – ${params.RTM_PROJECT}/${params.TEST_EXECUTION}"
          def body  = """
          <p>Automated RTM Test Execution report for <b>${params.RTM_PROJECT}/${params.TEST_EXECUTION}</b>.</p>
          <p>Generated via Jenkins Selenium pipeline.</p>
          """

          bat """
            .venv\\Scripts\\pip install requests
            .venv\\Scripts\\python scripts\\confluence_publish.py ^
              --space "%CONFLUENCE_SPACE%" ^
              --title "${title}" ^
              --body "${body}" ^
              --attach "%REPORT_FILE%"
          """
        }
      }
    }

    // -------------------------------------------------------------
    // Stage 5: Send Email Notification
    // -------------------------------------------------------------
    stage('Email Notification') {
      steps {
        script {
          echo "📧 Sending email notification with RTM report attachment..."

          def subject = "RTM Test Execution Report – ${params.RTM_PROJECT}/${params.TEST_EXECUTION}"
          def body = """Hi Team,

The RTM Test Execution report for project **${params.RTM_PROJECT}**, execution **${params.TEST_EXECUTION}**
has been successfully generated, published to Confluence, and is attached to this email.

Regards,
Jenkins Automated Pipeline
"""
          writeFile file: 'email_body.txt', text: body
        }

        bat """
          .venv\\Scripts\\python scripts\\send_email.py ^
            --subject "RTM Test Execution Report – %RTM_PROJECT%/%TEST_EXECUTION%" ^
            --body "email_body.txt" ^
            --to "%REPORT_TO%" ^
            --attach "%REPORT_FILE%"
        """
      }
    }
  }

  // ---------------------------------------------------------------
  // 🧾 Post Actions
  // ---------------------------------------------------------------
  post {
    always {
      echo '📜 Pipeline execution completed.'
    }
    success {
      echo '✅ RTM Report exported, published to Confluence, and emailed successfully.'
    }
    failure {
      echo '❌ Pipeline failed — please review Jenkins console logs and export.out.'
    }
  }
}
