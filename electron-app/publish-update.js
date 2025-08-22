const { publish } = require('electron-publisher-github');
const { build } = require('electron-builder');
const path = require('path');

async function publishUpdate() {
  try {
    console.log('🚀 Publishing update to GitHub...');
    
    // Build the application
    console.log('📦 Building application...');
    await build({
      config: {
        appId: 'com.setportfolio.desktop',
        productName: 'SET Portfolio Manager',
        directories: {
          output: 'dist-cross-platform'
        },
        publish: [
          {
            provider: 'github',
            owner: 'ppwcr',
            repo: 'my-portfolio',
            private: false
          }
        ],
        win: {
          target: [
            {
              target: 'nsis',
              arch: ['x64', 'arm64']
            },
            {
              target: 'portable',
              arch: ['x64', 'arm64']
            }
          ]
        }
      }
    });
    
    console.log('✅ Build completed successfully!');
    console.log('📤 Publishing to GitHub releases...');
    
    // Publish to GitHub
    await publish({
      provider: 'github',
      owner: 'ppwcr',
      repo: 'my-portfolio',
      private: false,
      releaseType: 'release',
      draft: false,
      prerelease: false
    });
    
    console.log('🎉 Update published successfully!');
    console.log('📋 Users will be notified of the update automatically.');
    
  } catch (error) {
    console.error('❌ Error publishing update:', error);
    process.exit(1);
  }
}

// Run the publish function
publishUpdate();
