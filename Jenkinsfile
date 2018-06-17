def image
def image_base
def image_version
def image_router

pipeline {
  agent any

  stages {
    stage('Build base image') {
      steps {
        script {
          // Ensure that the base image is up-to-date
          image_base = docker.image('python:3.6.5-slim-stretch')
          image_base.pull()
          image = docker.build('wizardsofindustry/aorta')
          image_router = docker.build('wizardsofindustry/aorta-router',
            "-f Dockerfile.router")
        }
      }
    }

    stage('Build router image') {
      steps {
        script {
          image_router = docker.build('wizardsofindustry/aorta-router',
            "-f Dockerfile.router")
        }
      }
    }

    stage('Push to Docker Hub') {
      when {
        expression {
          return env.BRANCH_NAME == 'master'
        }
      }
      steps {
        script {
          image_version = readFile('version.info').trim()
          withDockerRegistry([ credentialsId: 'sg-docker-credentials' ]) {
            image.push("latest")
            image.push("${image_version}")
            image_router.push("latest")
            image_router.push("${image_version}")
          }
        }
      }
    }
  } // end stages

  post {
    success {
      slackSend(
        color: "#2EB886",
        message: "Success: Job ${env.JOB_NAME} [${env.BUILD_NUMBER}] (${env.BUILD_URL})")
    }
    failure {
      slackSend(
        color: "#CC0000",
        message: "Failed: Job ${env.JOB_NAME} [${env.BUILD_NUMBER}] (${env.BUILD_URL})")
    }
  }

} // end pipeline
