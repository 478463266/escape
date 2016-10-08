#!groovy
timestamps {
    node {
        checkout scm
        // The Dockerfile needs credentials to update submodules from Git
        sh '''
        mkdir -p docker/.ssh
        rm docker/.ssh/*
        cp ~/.ssh/id_rsa* docker/.ssh
        ssh-keygen -F 5gexgit.tmit.bme.hu > docker/.ssh/known_hosts
        '''
        docker.withRegistry('https://5gex.tmit.bme.hu') {
            def image = docker.build("escape:2.0.0.${env.BUILD_NUMBER}", '--build-arg "ESC_INSTALL_PARAMS=c -p 5gex" .')
            image.push()
            image.push('latest')
        }
    }
}
