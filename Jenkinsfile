pipeline {
  agent any
  options { timestamps(); ansiColor('xterm') }

  parameters {
    string(name: 'RTM_PROJECT',   defaultValue: 'RTM-DEMO',        description: 'RTM Project Key')
    string(name: 'TEST_EXECUTION',defaultValue: 'RD-4',description: 'RTM Test Execution Key')
    choice(name: 'REPORT_FORMAT', choices: ['html','pdf'], description: 'RTM export format')
  }

  environment {
    // Jira/RTM (bind from Jenkins credentials where possible)
    JIRA_BASE               = credentials('jira-base')         // or plain text
    JIRA_USER               = credentials('jira-user')
    JIRA_TOKEN              = credentials('jira-token')
    RTM_EXPORT_URL_TEMPLATE = credentials('rtm-export-url-template')

    // Confluence
    CONFLUENCE_BASE   = credentials('confluence-base')
    CONFLUENCE_USER   = credentials('confluence-user')
    CONFLUENCE_TOKEN  = credentials('confluence-token')
    CONFLUENCE_SPACE  = 'DEV'
    CONFLUENCE_TITLE  = "Test Execution Report – ${RTM_PROJECT}/${TEST_EXECUTION}"
    // CONFLUENCE_PARENT_ID = '123456' // optional

    // Email
    SMTP_HOST   = credentials('smtp-host')
    SMTP_PORT   = '587'
    SMTP_USER   = credentials('smtp-user')
    SMTP_PASS   = credentials('smtp-pass')
    REPORT_FROM = credentials('sender-email')
    REPORT_TO   = credentials('multi-receivers') // override per-job if needed

    PYTHONIOENCODING = 'utf-8'
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Set up Python venv') {
      steps {
        // Windows-friendly; adapt to Linux with sh & source
        bat """
          if not exist .venv python -m venv .venv
          .venv\\Scripts\\python -m pip install --upgrade pip
          .venv\\Scripts\\pip install -r requirements.txt
        """
      }
    }

    stage('Export RTM report') {
      steps {
        bat """
          .venv\\Scripts\\python scripts\\rtm_export.py ^
            --rtm-project "%RTM_PROJECT%" ^
            --test-exec "%TEST_EXECUTION%" ^
            --format "%REPORT_FORMAT%" ^
            --outdir report > export.out
        """
        script {
          // read artifact path from script stdout
          def out = readFile('export.out')
          def m = (out =~ /ARTIFACT_PATH=(.+)\s*$/)
          if (!m) error "Failed to parse ARTIFACT_PATH from export.out"
          env.REPORT_FILE = m[0][1].trim()
          echo "Report file: ${env.REPORT_FILE}"
        }
      }
      post {
        success { archiveArtifacts artifacts: 'report/**', fingerprint: true }
      }
    }

    stage('Publish to Confluence') {
      steps {
        bat """
          .venv\\Scripts\\python scripts\\confluence_publish.py ^
            --space "%CONFLUENCE_SPACE%" ^
            --title "%CONFLUENCE_TITLE%" ^
            --body "<p>Automated RTM Test Execution report for <b>%RTM_PROJECT% / %TEST_EXECUTION%</b>.</p>" ^
            --attach "%REPORT_FILE%"
        """
        script {
          def out = bat(returnStdout: true, script: '.venv\\Scripts\\python -c "print(\'done\')"')
          // We just used stdout in the step above; to capture the page link, you can write to a file as in export stage.
        }
      }
    }

    stage('Email notification') {
      steps {
        // Build a simple body and send
        script {
          def subject = "RTM Test Execution Report – ${params.RTM_PROJECT}/${params.TEST_EXECUTION}"
          def body    = "Hi Team,\n\nRTM report is attached.\n\nRegards,\nJenkins"
          writeFile file: 'email_body.txt', text: body
        }
        bat """
          .venv\\Scripts\\python scripts\\send_email.py ^
            --subject "RTM Test Execution Report – %RTM_PROJECT%/%TEST_EXECUTION%" ^
            --body    "%CD%\\email_body.txt" ^
            --to      "%REPORT_TO%" ^
            --attach  "%REPORT_FILE%"
        """
      }
    }
  }

  post {
    always { echo 'Pipeline finished.' }
  }
}
