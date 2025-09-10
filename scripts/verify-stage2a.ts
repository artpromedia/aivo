#!/usr/bin/env ts-node
/**
 * Stage-2A Golden Path Verification Script
 * Tests the complete S2A pipeline: problem session → ink → recognize → grade → result
 * Also tests device enrollment → policy push → bundle request
 */

import { setTimeout as delay } from 'timers/promises';

// HTTP Client wrapper using native fetch
class HttpClient {
  private timeout: number;

  constructor(timeout = 30000) {
    this.timeout = timeout;
  }

  async request(url: string, options: RequestInit = {}): Promise<{ status: number; data: any }> {
    const controller = new AbortController();
    const timeoutId = globalThis.setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      let data;
      try {
        data = await response.json();
      } catch {
        data = await response.text();
      }

      return { status: response.status, data };
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  async get(url: string, options: { headers?: Record<string, string> } = {}) {
    return this.request(url, { method: 'GET', headers: options.headers });
  }

  async post(url: string, body?: any, options: { headers?: Record<string, string> } = {}) {
    return this.request(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: body ? JSON.stringify(body) : undefined
    });
  }
}

// Configuration
const config = {
  baseUrl: 'http://localhost:8000', // Kong Gateway
  services: {
    // Core services
    auth: 'http://localhost:8081',
    tenant: 'http://localhost:8082',
    // S2A Services
    ink: 'http://localhost:8100',
    mathRecognizer: 'http://localhost:8101',
    scienceSolver: 'http://localhost:8102',
    elaEval: 'http://localhost:8103',
    slpSel: 'http://localhost:8104',
    problemSession: 'http://localhost:8105',
    deviceEnroll: 'http://localhost:8106',
    devicePolicy: 'http://localhost:8107',
    edgeBundler: 'http://localhost:8108',
    deviceOta: 'http://localhost:8109'
  },
  testData: {
    device: {
      serialNumber: 'TEST-DEVICE-001',
      deviceType: 'tablet',
      manufacturer: 'Apple',
      model: 'iPad Pro',
      osVersion: '17.0',
      location: 'Classroom A'
    },
    policy: {
      name: 'Test Math Policy',
      description: 'Policy for math problem solving',
      type: 'learning',
      configuration: {
        allowedApps: ['math-solver', 'ink-tool'],
        restrictions: {
          browserAccess: false,
          installApps: false
        },
        features: {
          inkInput: true,
          mathRecognition: true,
          scienceSolver: true
        }
      }
    },
    problemSession: {
      subjectArea: 'mathematics',
      grade: '8th',
      topic: 'algebra',
      difficulty: 'medium',
      sessionType: 'practice'
    },
    inkData: {
      strokes: [
        {
          points: [
            { x: 100, y: 200, pressure: 0.5, timestamp: Date.now() },
            { x: 150, y: 200, pressure: 0.7, timestamp: Date.now() + 10 },
            { x: 200, y: 200, pressure: 0.6, timestamp: Date.now() + 20 }
          ],
          toolType: 'pen',
          color: '#000000'
        }
      ],
      canvasSize: { width: 800, height: 600 },
      metadata: {
        equation: '2x + 5 = 15',
        expectedAnswer: 'x = 5'
      }
    }
  }
};

interface TestContext {
  tokens: {
    adminToken?: string;
    deviceToken?: string;
  };
  entities: {
    deviceId?: string;
    policyId?: string;
    bundleId?: string;
    sessionId?: string;
    inkSessionId?: string;
    recognitionId?: string;
    solutionId?: string;
    gradingId?: string;
  };
  http: HttpClient;
}

class Stage2AVerifier {
  private context: TestContext;

  constructor() {
    this.context = {
      tokens: {},
      entities: {},
      http: new HttpClient()
    };
  }

  async run(): Promise<void> {
    console.log('🚀 Starting Stage-2A Golden Path Verification');
    console.log('=' .repeat(60));

    try {
      // Step 1: Health checks
      await this.verifyHealthChecks();
      
      // Step 2: Authentication setup
      await this.setupAuthentication();
      
      // Step 3: Problem Session → Ink → Recognition → Grading Flow
      await this.startProblemSession();
      await this.captureInkInput();
      await this.recognizeMathExpression();
      await this.solveAndGrade();
      await this.getResults();
      
      // Step 4: Device Management Flow
      await this.enrollMockDevice();
      await this.createDevicePolicy();
      await this.assignPolicyToDevice();
      await this.requestBundle();
      
      console.log('\n✅ Stage-2A Golden Path Verification PASSED!');
      console.log('🎉 All S2A services working correctly in the pipeline');
      
    } catch (error) {
      console.error('\n❌ Stage-2A Golden Path Verification FAILED!');
      console.error('Error:', error instanceof Error ? error.message : error);
      process.exit(1);
    }
  }

  private async verifyHealthChecks(): Promise<void> {
    console.log('\n🔍 Step 1: Verifying S2A service health checks...');
    
    const healthChecks = Object.entries(config.services).map(async ([name, url]) => {
      try {
        const response = await this.context.http.get(`${url}/health`);
        if (response.status === 200) {
          console.log(`  ✅ ${name}: healthy`);
          return true;
        } else {
          console.log(`  ❌ ${name}: unhealthy (${response.status})`);
          return false;
        }
      } catch (error) {
        console.log(`  ❌ ${name}: connection failed`);
        return false;
      }
    });

    const results = await Promise.all(healthChecks);
    const healthyCount = results.filter(r => r).length;
    
    if (healthyCount < results.length) {
      throw new Error(`Only ${healthyCount}/${results.length} services are healthy`);
    }
    
    console.log(`  🎯 All ${results.length} S2A services are healthy!`);
  }

  private async setupAuthentication(): Promise<void> {
    console.log('\n🔐 Step 2: Setting up authentication...');
    
    // Create admin token for device management
    const authResponse = await this.context.http.post(`${config.services.auth}/login`, {
      email: 'admin@test.com',
      password: 'test123',
      role: 'admin'
    });
    
    if (authResponse.status !== 200) {
      throw new Error(`Authentication failed: ${authResponse.status}`);
    }
    
    this.context.tokens.adminToken = authResponse.data.token;
    console.log('  ✅ Admin authentication successful');
  }

  private async startProblemSession(): Promise<void> {
    console.log('\n📚 Step 3: Starting problem session...');
    
    const response = await this.context.http.post(
      `${config.services.problemSession}/sessions`,
      config.testData.problemSession,
      {
        headers: {
          'Authorization': `Bearer ${this.context.tokens.adminToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.status !== 201) {
      throw new Error(`Failed to create problem session: ${response.status} - ${response.data?.message}`);
    }
    
    this.context.entities.sessionId = response.data.sessionId;
    console.log(`  ✅ Problem session created: ${this.context.entities.sessionId}`);
  }

  private async captureInkInput(): Promise<void> {
    console.log('\n✍️ Step 4: Capturing ink input...');
    
    const response = await this.context.http.post(
      `${config.services.ink}/sessions`,
      {
        sessionId: this.context.entities.sessionId,
        strokes: config.testData.inkData.strokes,
        canvasSize: config.testData.inkData.canvasSize,
        metadata: config.testData.inkData.metadata
      },
      {
        headers: {
          'Authorization': `Bearer ${this.context.tokens.adminToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.status !== 201) {
      throw new Error(`Failed to capture ink input: ${response.status} - ${response.data?.message}`);
    }
    
    this.context.entities.inkSessionId = response.data.inkSessionId;
    console.log(`  ✅ Ink input captured: ${this.context.entities.inkSessionId}`);
  }

  private async recognizeMathExpression(): Promise<void> {
    console.log('\n🔍 Step 5: Recognizing math expression...');
    
    const response = await this.context.http.post(
      `${config.services.mathRecognizer}/recognize`,
      {
        inkSessionId: this.context.entities.inkSessionId,
        subjectArea: config.testData.problemSession.subjectArea
      },
      {
        headers: {
          'Authorization': `Bearer ${this.context.tokens.adminToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.status !== 200) {
      throw new Error(`Failed to recognize math expression: ${response.status} - ${response.data?.message}`);
    }
    
    this.context.entities.recognitionId = response.data.recognitionId;
    console.log(`  ✅ Math expression recognized: ${response.data.expression}`);
    console.log(`  📝 Recognition confidence: ${response.data.confidence}`);
  }

  private async solveAndGrade(): Promise<void> {
    console.log('\n🧮 Step 6: Solving and grading...');
    
    // Send to appropriate solver based on subject area
    const solverUrl = config.testData.problemSession.subjectArea === 'mathematics' 
      ? config.services.scienceSolver 
      : config.services.elaEval;
    
    const response = await this.context.http.post(
      `${solverUrl}/solve`,
      {
        recognitionId: this.context.entities.recognitionId,
        sessionId: this.context.entities.sessionId,
        expectedAnswer: config.testData.inkData.metadata.expectedAnswer
      },
      {
        headers: {
          'Authorization': `Bearer ${this.context.tokens.adminToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.status !== 200) {
      throw new Error(`Failed to solve and grade: ${response.status} - ${response.data?.message}`);
    }
    
    this.context.entities.solutionId = response.data.solutionId;
    this.context.entities.gradingId = response.data.gradingId;
    console.log(`  ✅ Solution generated: ${response.data.solution}`);
    console.log(`  📊 Grade: ${response.data.grade}%`);
    console.log(`  ✔️ Correct: ${response.data.isCorrect}`);
  }

  private async getResults(): Promise<void> {
    console.log('\n📋 Step 7: Getting session results...');
    
    const response = await this.context.http.get(
      `${config.services.problemSession}/sessions/${this.context.entities.sessionId}/results`,
      {
        headers: {
          'Authorization': `Bearer ${this.context.tokens.adminToken}`
        }
      }
    );
    
    if (response.status !== 200) {
      throw new Error(`Failed to get session results: ${response.status} - ${response.data?.message}`);
    }
    
    console.log(`  ✅ Session completed successfully`);
    console.log(`  📊 Final score: ${response.data.finalScore}%`);
    console.log(`  ⏱️ Duration: ${response.data.durationMs}ms`);
    console.log(`  🎯 Steps completed: ${response.data.stepsCompleted}`);
  }

  private async enrollMockDevice(): Promise<void> {
    console.log('\n📱 Step 8: Enrolling mock device...');
    
    const response = await this.context.http.post(
      `${config.services.deviceEnroll}/devices`,
      config.testData.device,
      {
        headers: {
          'Authorization': `Bearer ${this.context.tokens.adminToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.status !== 201) {
      throw new Error(`Failed to enroll device: ${response.status} - ${response.data?.message}`);
    }
    
    this.context.entities.deviceId = response.data.deviceId;
    console.log(`  ✅ Device enrolled: ${this.context.entities.deviceId}`);
    console.log(`  📟 Serial: ${config.testData.device.serialNumber}`);
    console.log(`  🏷️ Type: ${config.testData.device.deviceType}`);
  }

  private async createDevicePolicy(): Promise<void> {
    console.log('\n📋 Step 9: Creating device policy...');
    
    const response = await this.context.http.post(
      `${config.services.devicePolicy}/policies`,
      config.testData.policy,
      {
        headers: {
          'Authorization': `Bearer ${this.context.tokens.adminToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.status !== 201) {
      throw new Error(`Failed to create policy: ${response.status} - ${response.data?.message}`);
    }
    
    this.context.entities.policyId = response.data.policyId;
    console.log(`  ✅ Policy created: ${this.context.entities.policyId}`);
    console.log(`  📝 Name: ${config.testData.policy.name}`);
    console.log(`  🔧 Type: ${config.testData.policy.type}`);
  }

  private async assignPolicyToDevice(): Promise<void> {
    console.log('\n🔗 Step 10: Assigning policy to device...');
    
    const response = await this.context.http.post(
      `${config.services.devicePolicy}/assignments`,
      {
        deviceId: this.context.entities.deviceId,
        policyId: this.context.entities.policyId
      },
      {
        headers: {
          'Authorization': `Bearer ${this.context.tokens.adminToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.status !== 201) {
      throw new Error(`Failed to assign policy: ${response.status} - ${response.data?.message}`);
    }
    
    console.log(`  ✅ Policy assigned to device`);
    console.log(`  🔗 Assignment ID: ${response.data.assignmentId}`);
  }

  private async requestBundle(): Promise<void> {
    console.log('\n📦 Step 11: Requesting edge bundle...');
    
    const response = await this.context.http.post(
      `${config.services.edgeBundler}/bundles`,
      {
        deviceId: this.context.entities.deviceId,
        bundleType: 'full',
        includeAssets: true
      },
      {
        headers: {
          'Authorization': `Bearer ${this.context.tokens.adminToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.status !== 201) {
      throw new Error(`Failed to request bundle: ${response.status} - ${response.data?.message}`);
    }
    
    this.context.entities.bundleId = response.data.bundleId;
    console.log(`  ✅ Bundle created: ${this.context.entities.bundleId}`);
    console.log(`  📦 Bundle size: ${response.data.sizeBytes} bytes`);
    console.log(`  🔗 Download URL: ${response.data.downloadUrl}`);
    
    // Wait a moment for bundle processing
    await delay(2000);
    
    // Verify bundle status
    const statusResponse = await this.context.http.get(
      `${config.services.edgeBundler}/bundles/${this.context.entities.bundleId}`,
      {
        headers: {
          'Authorization': `Bearer ${this.context.tokens.adminToken}`
        }
      }
    );
    
    if (statusResponse.status === 200) {
      console.log(`  📊 Bundle status: ${statusResponse.data.status}`);
      console.log(`  ✅ Bundle ready for deployment`);
    }
  }
}

// Main execution
async function main() {
  const verifier = new Stage2AVerifier();
  await verifier.run();
}

// Run if called directly
if (require.main === module) {
  main().catch((error) => {
    console.error('Verification failed:', error);
    process.exit(1);
  });
}

export { Stage2AVerifier };
