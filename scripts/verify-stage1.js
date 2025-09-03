#!/usr/bin/env node
/**
 * Stage-1 Golden Path Verification Script (JavaScript)
 * Simplified version for quick execution without TypeScript dependencies
 */

const axios = require('axios');
const { setTimeout } = require('timers/promises');

// Configuration
const config = {
  baseUrl: 'http://localhost:8000',
  services: {
    auth: 'http://localhost:8081',
    tenant: 'http://localhost:8082', 
    payment: 'http://localhost:8083',
    learner: 'http://localhost:8084',
    enrollment: 'http://localhost:8085',
    inference: 'http://localhost:8086',
    assessment: 'http://localhost:8087',
    approval: 'http://localhost:8088',
    iep: 'http://localhost:8089',
    notification: 'http://localhost:8090',
    adminPortal: 'http://localhost:8091',
    orchestrator: 'http://localhost:8092'
  }
};

class Stage1Verifier {
  constructor() {
    this.context = {
      tokens: {},
      entities: {},
      http: axios.create({
        timeout: 30000,
        validateStatus: () => true
      })
    };
  }

  async run() {
    console.log('🚀 Starting Stage-1 Golden Path Verification');
    console.log('=' .repeat(60));

    try {
      await this.verifyHealthChecks();
      console.log('\n✅ Stage-1 Golden Path Verification PASSED!');
      console.log('🎉 All services are healthy and ready');
      
    } catch (error) {
      console.error('\n❌ Stage-1 Golden Path Verification FAILED!');
      console.error('Error:', error.message);
      process.exit(1);
    }
  }

  async verifyHealthChecks() {
    console.log('\n🔍 Verifying service health checks...');
    
    const results = [];
    
    for (const [name, url] of Object.entries(config.services)) {
      try {
        const response = await this.context.http.get(`${url}/health`);
        if (response.status === 200) {
          console.log(`  ✅ ${name}: healthy`);
          results.push(true);
        } else {
          console.log(`  ❌ ${name}: unhealthy (${response.status})`);
          results.push(false);
        }
      } catch (error) {
        console.log(`  ❌ ${name}: connection failed`);
        results.push(false);
      }
    }

    const healthyCount = results.filter(r => r).length;
    
    if (healthyCount < results.length) {
      throw new Error(`Only ${healthyCount}/${results.length} services are healthy`);
    }
    
    console.log(`  🎯 All ${results.length} services are healthy`);
  }
}

// Run the verification
if (require.main === module) {
  const verifier = new Stage1Verifier();
  verifier.run().catch(error => {
    console.error('Verification failed:', error);
    process.exit(1);
  });
}

module.exports = Stage1Verifier;
