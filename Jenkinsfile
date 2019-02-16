def versionstr = "1.0.${env.BUILD_NUMBER}"
def branch = "master"
if (env.BRANCH_NAME)
{
    branch = "${env.BRANCH_NAME}"
}
node('master') {
  try{
      currentBuild.result = 'SUCCESS'
      stage('Checkout'){
        deleteDir()

        checkout scm
        sh "sed -i 's/0.0.0/${versionstr}/g' setup.py"
        dir('docker/unit') {
          sh "sed -i 's/0.0.0/${versionstr}/g' docker-compose.yml"
        }
        dir('autotrader/base') {
          sh "sed -i 's/1.0.0/${versionstr}/g' version.py"
        }
        withCredentials([file(credentialsId: 'autotradertest', variable: 'FILE')]) {
          sh 'cp ${FILE} config_test.ini'
        }
      }

      stage('BuildDocker'){
        dir('docker/unit/data') {
          sh 'unzip test_db_v1.zip'
        }

        dir('docker/unit') {
            sh 'docker stop autotrader_test || true && docker rm autotrader_test || true'
            sh 'docker stop mysql_test || true && docker rm mysql_test || true'
            sh 'docker-compose down'
            sh 'docker-compose rm -v --force'
            sh 'docker-compose build'
            sh 'docker-compose up -d --force-recreate'
        }
      }

      stage('CodeQualityChecker') {
        sh 'docker exec autotrader_test pylint -f parseable -d I0011,R0801 autotrader | tee pylint.out'
        step([
            $class                     : 'WarningsPublisher',
            parserConfigurations       : [[
                                                  parserName: 'PYLint',
                                                  pattern   : '**/pylint.out'
                                          ]],
            unstableTotalAll           : '300',
            usePreviousBuildAsReference: true
        ])
      }


      stage('UnitTest') {
            try {
              sh 'docker exec -e NUMBA_DISABLE_JIT=1 -e CONFIG_FILE=config_test.ini autotrader_test nose2  -c unittest.cfg'
            } catch (Exception err) {
              currentBuild.result = 'FAILURE'
            }
            sh 'docker cp autotrader_test:/usr/src/app/report.xml .'
            junit('**/report.xml')
            sh 'docker exec autotrader_test coverage html'
            sh 'docker exec autotrader_test coverage xml'
            sh 'docker cp autotrader_test:/usr/src/app/coverage.xml .'
            step([$class: 'CoberturaPublisher', autoUpdateHealth: false, autoUpdateStability: false, coberturaReportFile: '**/coverage.xml', failUnhealthy: false, failUnstable: false, maxNumberOfBuilds: 0, onlyStable: false, sourceEncoding: 'ASCII', zoomCoverageChart: false])
            if (currentBuild.result.equals('FAILURE')){
               dir('docker/unit') {
                  sh 'docker-compose stop'
               }
               sh 'exit 1'
            }
       }

      stage('Build') {
          if("${branch}" == "master")
          {
              sh 'docker exec autotrader_test python setup.py bdist_wheel'
              sh "docker cp autotrader_test:/usr/src/app/dist/autotrader-${versionstr}-py3-none-any.whl ."
              archiveArtifacts  artifacts: '**/autotrader*.whl', onlyIfSuccessful: true
              dir('docker/unit') {
                 sh 'docker-compose stop'
              }
              sh "docker build  -f docker/release/Dockerfile -t autotrader:latest -t autotrader:${versionstr} ."
              sh "docker save autotrader:latest | gzip -c > autotrader_docker${versionstr}.tgz"
              archiveArtifacts artifacts: '**/autotrader_docker*.tgz', onlyIfSuccessful: true
              stash includes: "autotrader_docker${versionstr}.tgz", name: 'dockerfile'
          }
      }
      HOSTS = ["vm1", "vm2"]
      def branches = [:]
      for (h in HOSTS)
      {
          def host = h  // fresh variable per iteration; it will be mutated
          branches[host] = {
              stage("Deploy ${host}")
              {
                  node(host)
                  {
                      sh 'docker rm autotrader || exit 0'
                      sh 'rm -rf autotrader_docker*.tgz || exit 0'
                      unstash 'dockerfile'
                      withCredentials([file(credentialsId: 'autotraderlive_v2', variable: 'FILE')])
                      {
                          sh 'gunzip -c autotrader_docker*.tgz | docker load'
                          sh 'docker create --name autotrader autotrader:latest'
                          sh "docker cp ${FILE}  autotrader:/usr/src/app/config_live.ini"
                          sh 'docker commit autotrader autotrader'
                      }
                  }
              }
         }
      }
      parallel branches
      stage('Clean') {
           cleanWs()
      }
  }
  catch (err) {
    currentBuild.result = 'FAILURE'
  }
  finally {
      if(currentBuild.result != 'SUCCESS')
      {
        def mailRecipients = "slash.gordon.dev@gmail.com"
        def emailBody = '${SCRIPT, template="groovy-html.template"}'
        def emailSubject = "${env.JOB_NAME} - Build# ${env.BUILD_NUMBER} - ${currentBuild.result}"
        emailext(mimeType: 'text/html', subject: emailSubject, to: mailRecipients, body: emailBody)
      }
  }
}
