#!/usr/bin/env ts-node
/**
 * Stage-1 Golden Path Verification Script
 * Tests the complete educational platform pipeline from district creation to IEP approval
 */

import axios, { AxiosInstance } from 'axios';
import { setTimeout } from 'timers/promises';

// Configuration
const config = {
  baseUrl: 'http://localhost:8000', // Kong Gateway
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
  },
  testData: {
    district: {
      name: 'Test Valley School District',
      type: 'public',
      address: '123 Education Ave, Learning City, LC 12345',
      contactEmail: 'admin@testvalley.edu'
    },
    school: {
      name: 'Valley Elementary School',
      type: 'elementary',
      address: '456 School St, Learning City, LC 12345',
      principalEmail: 'principal@valleyelementary.edu'
    },
    guardian: {
      firstName: 'Sarah',
      lastName: 'Johnson',
      email: 'sarah.johnson@email.com',
      phone: '+1-555-0123',
      address: '789 Parent Ln, Learning City, LC 12345'
    },
    learner: {
      firstName: 'Alex',
      lastName: 'Johnson',
      dateOfBirth: '2015-03-15',
      grade: '3rd',
      specialNeeds: true,
      disabilities: ['learning_disability', 'adhd']
    }
  }
};

interface TestContext {
  tokens: {
    districtAdmin?: string;
    guardian?: string;
    teacher?: string;
  };
  entities: {
    districtId?: string;
    schoolId?: string;
    guardianId?: string;
    learnerId?: string;
    enrollmentId?: string;
    assessmentId?: string;
    iepId?: string;
    approvalRequestId?: string;
  };
  http: AxiosInstance;
}

class Stage1Verifier {
  private context: TestContext;

  constructor() {
    this.context = {
      tokens: {},
      entities: {},
      http: axios.create({
        timeout: 30000,
        validateStatus: () => true // Don't throw on non-2xx status codes
      })
    };
  }

  async run(): Promise<void> {
    console.log('🚀 Starting Stage-1 Golden Path Verification');
    console.log('=' .repeat(60));

    try {
      // Step 1: Health checks
      await this.verifyHealthChecks();
      
      // Step 2: Create district and school infrastructure
      await this.createDistrict();
      await this.createSchool();
      await this.purchaseSeats();
      
      // Step 3: Guardian registration and learner creation
      await this.registerGuardian();
      await this.createLearner();
      await this.enrollLearner();
      
      // Step 4: Assessment and IEP workflow
      await this.waitForOrchestratorReady();
      await this.startBaselineAssessment();
      await this.finishBaselineAssessment();
      await this.draftIEP();
      await this.submitIEP();
      await this.approveIEP();
      
      // Step 5: Verify admin portal summary
      await this.verifyAdminPortalSummary();
      
      console.log('\n✅ Stage-1 Golden Path Verification PASSED!');
      console.log('🎉 All services working correctly in the pipeline');
      
    } catch (error) {
      console.error('\n❌ Stage-1 Golden Path Verification FAILED!');
      console.error('Error:', error instanceof Error ? error.message : error);
      process.exit(1);
    }
  }

  private async verifyHealthChecks(): Promise<void> {
    console.log('\n🔍 Step 1: Verifying service health checks...');
    
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
    
    console.log(`  🎯 All ${results.length} services are healthy`);
  }

  private async createDistrict(): Promise<void> {
    console.log('\n🏛️  Step 2a: Creating district...');
    
    // First register district admin
    const adminResponse = await this.context.http.post(`${config.services.auth}/register`, {
      email: config.testData.district.contactEmail,
      password: 'District123!',
      firstName: 'District',
      lastName: 'Administrator',
      role: 'district_admin'
    });
    
    if (adminResponse.status !== 201) {
      throw new Error(`Failed to register district admin: ${adminResponse.status}`);
    }
    
    // Login and get token
    const loginResponse = await this.context.http.post(`${config.services.auth}/login`, {
      email: config.testData.district.contactEmail,
      password: 'District123!'
    });
    
    if (loginResponse.status !== 200) {
      throw new Error(`Failed to login district admin: ${loginResponse.status}`);
    }
    
    this.context.tokens.districtAdmin = loginResponse.data.token;
    
    // Create district
    const districtResponse = await this.context.http.post(
      `${config.services.tenant}/districts`,
      config.testData.district,
      {
        headers: { Authorization: `Bearer ${this.context.tokens.districtAdmin}` }
      }
    );
    
    if (districtResponse.status !== 201) {
      throw new Error(`Failed to create district: ${districtResponse.status}`);
    }
    
    this.context.entities.districtId = districtResponse.data.id;
    console.log(`  ✅ District created: ${this.context.entities.districtId}`);
  }

  private async createSchool(): Promise<void> {
    console.log('\n🏫 Step 2b: Creating school...');
    
    const schoolResponse = await this.context.http.post(
      `${config.services.tenant}/districts/${this.context.entities.districtId}/schools`,
      config.testData.school,
      {
        headers: { Authorization: `Bearer ${this.context.tokens.districtAdmin}` }
      }
    );
    
    if (schoolResponse.status !== 201) {
      throw new Error(`Failed to create school: ${schoolResponse.status}`);
    }
    
    this.context.entities.schoolId = schoolResponse.data.id;
    console.log(`  ✅ School created: ${this.context.entities.schoolId}`);
  }

  private async purchaseSeats(): Promise<void> {
    console.log('\n💳 Step 2c: Purchasing seats...');
    
    const purchaseResponse = await this.context.http.post(
      `${config.services.payment}/purchase`,
      {
        districtId: this.context.entities.districtId,
        seatCount: 100,
        planType: 'standard',
        paymentMethod: {
          type: 'test_card',
          cardNumber: '4242424242424242'
        }
      },
      {
        headers: { Authorization: `Bearer ${this.context.tokens.districtAdmin}` }
      }
    );
    
    if (purchaseResponse.status !== 201) {
      throw new Error(`Failed to purchase seats: ${purchaseResponse.status}`);
    }
    
    console.log(`  ✅ Purchased 100 seats for district`);
  }

  private async registerGuardian(): Promise<void> {
    console.log('\n👨‍👩‍👧‍👦 Step 3a: Registering guardian...');
    
    const guardianResponse = await this.context.http.post(`${config.services.auth}/register`, {
      email: config.testData.guardian.email,
      password: 'Guardian123!',
      firstName: config.testData.guardian.firstName,
      lastName: config.testData.guardian.lastName,
      role: 'guardian',
      phone: config.testData.guardian.phone,
      address: config.testData.guardian.address
    });
    
    if (guardianResponse.status !== 201) {
      throw new Error(`Failed to register guardian: ${guardianResponse.status}`);
    }
    
    // Login guardian
    const loginResponse = await this.context.http.post(`${config.services.auth}/login`, {
      email: config.testData.guardian.email,
      password: 'Guardian123!'
    });
    
    if (loginResponse.status !== 200) {
      throw new Error(`Failed to login guardian: ${loginResponse.status}`);
    }
    
    this.context.tokens.guardian = loginResponse.data.token;
    this.context.entities.guardianId = loginResponse.data.user.id;
    console.log(`  ✅ Guardian registered: ${this.context.entities.guardianId}`);
  }

  private async createLearner(): Promise<void> {
    console.log('\n👶 Step 3b: Creating learner...');
    
    const learnerResponse = await this.context.http.post(
      `${config.services.learner}/learners`,
      {
        ...config.testData.learner,
        guardianId: this.context.entities.guardianId,
        districtId: this.context.entities.districtId
      },
      {
        headers: { Authorization: `Bearer ${this.context.tokens.guardian}` }
      }
    );
    
    if (learnerResponse.status !== 201) {
      throw new Error(`Failed to create learner: ${learnerResponse.status}`);
    }
    
    this.context.entities.learnerId = learnerResponse.data.id;
    console.log(`  ✅ Learner created: ${this.context.entities.learnerId}`);
  }

  private async enrollLearner(): Promise<void> {
    console.log('\n📝 Step 3c: Enrolling learner...');
    
    const enrollmentResponse = await this.context.http.post(
      `${config.services.enrollment}/enroll`,
      {
        learnerId: this.context.entities.learnerId,
        schoolId: this.context.entities.schoolId,
        enrollmentType: 'guardian_initiated',
        requestedServices: ['special_education', 'speech_therapy']
      },
      {
        headers: { Authorization: `Bearer ${this.context.tokens.guardian}` }
      }
    );
    
    if (enrollmentResponse.status !== 201) {
      throw new Error(`Failed to enroll learner: ${enrollmentResponse.status}`);
    }
    
    this.context.entities.enrollmentId = enrollmentResponse.data.id;
    console.log(`  ✅ Learner enrolled: ${this.context.entities.enrollmentId}`);
  }

  private async waitForOrchestratorReady(): Promise<void> {
    console.log('\n🤖 Step 4a: Waiting for orchestrator readiness...');
    
    let attempts = 0;
    const maxAttempts = 30;
    
    while (attempts < maxAttempts) {
      try {
        const statusResponse = await this.context.http.get(
          `${config.services.orchestrator}/status/${this.context.entities.learnerId}`
        );
        
        if (statusResponse.status === 200 && statusResponse.data.status === 'READY') {
          console.log(`  ✅ Orchestrator ready for learner`);
          return;
        }
        
        console.log(`  ⏳ Waiting... (attempt ${attempts + 1}/${maxAttempts})`);
        await setTimeout(2000);
        attempts++;
        
      } catch (error) {
        attempts++;
        if (attempts >= maxAttempts) {
          throw new Error('Orchestrator did not become ready in time');
        }
        await setTimeout(2000);
      }
    }
    
    throw new Error('Orchestrator readiness timeout');
  }

  private async startBaselineAssessment(): Promise<void> {
    console.log('\n📊 Step 4b: Starting baseline assessment...');
    
    const assessmentResponse = await this.context.http.post(
      `${config.services.assessment}/assessments`,
      {
        learnerId: this.context.entities.learnerId,
        type: 'baseline',
        areas: ['reading', 'math', 'behavior', 'speech']
      },
      {
        headers: { Authorization: `Bearer ${this.context.tokens.guardian}` }
      }
    );
    
    if (assessmentResponse.status !== 201) {
      throw new Error(`Failed to start assessment: ${assessmentResponse.status}`);
    }
    
    this.context.entities.assessmentId = assessmentResponse.data.id;
    console.log(`  ✅ Baseline assessment started: ${this.context.entities.assessmentId}`);
  }

  private async finishBaselineAssessment(): Promise<void> {
    console.log('\n✅ Step 4c: Finishing baseline assessment...');
    
    // Submit assessment results
    const resultsResponse = await this.context.http.post(
      `${config.services.assessment}/assessments/${this.context.entities.assessmentId}/results`,
      {
        results: {
          reading: { score: 75, grade_level: '2.5', areas_of_concern: ['comprehension'] },
          math: { score: 82, grade_level: '3.0', areas_of_concern: ['word_problems'] },
          behavior: { score: 68, concerns: ['attention', 'social_interaction'] },
          speech: { score: 70, concerns: ['articulation', 'fluency'] }
        },
        recommendations: [
          'Specialized reading instruction',
          'Speech therapy services',
          'Behavioral support plan'
        ]
      },
      {
        headers: { Authorization: `Bearer ${this.context.tokens.guardian}` }
      }
    );
    
    if (resultsResponse.status !== 200) {
      throw new Error(`Failed to submit assessment results: ${resultsResponse.status}`);
    }
    
    console.log(`  ✅ Assessment results submitted`);
  }

  private async draftIEP(): Promise<void> {
    console.log('\n📋 Step 4d: Drafting IEP...');
    
    const iepResponse = await this.context.http.post(
      `${config.services.iep}/ieps`,
      {
        learnerId: this.context.entities.learnerId,
        assessmentId: this.context.entities.assessmentId,
        goals: [
          {
            area: 'reading',
            goal: 'Improve reading comprehension to grade level by end of year',
            measurable_objectives: ['Read 3rd grade texts with 80% comprehension']
          },
          {
            area: 'speech',
            goal: 'Improve speech articulation and fluency',
            measurable_objectives: ['Produce target sounds with 90% accuracy']
          }
        ],
        services: [
          { type: 'special_education', frequency: '5x/week', duration: '60min' },
          { type: 'speech_therapy', frequency: '2x/week', duration: '30min' }
        ],
        accommodations: [
          'Extended time on tests',
          'Preferential seating',
          'Frequent breaks'
        ]
      },
      {
        headers: { Authorization: `Bearer ${this.context.tokens.guardian}` }
      }
    );
    
    if (iepResponse.status !== 201) {
      throw new Error(`Failed to draft IEP: ${iepResponse.status}`);
    }
    
    this.context.entities.iepId = iepResponse.data.id;
    console.log(`  ✅ IEP drafted: ${this.context.entities.iepId}`);
  }

  private async submitIEP(): Promise<void> {
    console.log('\n📤 Step 4e: Submitting IEP for approval...');
    
    const submitResponse = await this.context.http.post(
      `${config.services.approval}/approval-requests`,
      {
        type: 'iep_approval',
        entityId: this.context.entities.iepId,
        requestedBy: this.context.entities.guardianId,
        districtId: this.context.entities.districtId,
        schoolId: this.context.entities.schoolId,
        urgency: 'normal',
        documents: [`iep_${this.context.entities.iepId}.pdf`]
      },
      {
        headers: { Authorization: `Bearer ${this.context.tokens.guardian}` }
      }
    );
    
    if (submitResponse.status !== 201) {
      throw new Error(`Failed to submit IEP for approval: ${submitResponse.status}`);
    }
    
    this.context.entities.approvalRequestId = submitResponse.data.id;
    console.log(`  ✅ IEP submitted for approval: ${this.context.entities.approvalRequestId}`);
  }

  private async approveIEP(): Promise<void> {
    console.log('\n👍 Step 4f: Approving IEP...');
    
    // Simulate district admin approving the IEP
    const approvalResponse = await this.context.http.post(
      `${config.services.approval}/approval-requests/${this.context.entities.approvalRequestId}/approve`,
      {
        decision: 'approved',
        comments: 'IEP meets all requirements and is approved for implementation',
        approvedBy: 'district_admin',
        effectiveDate: new Date().toISOString()
      },
      {
        headers: { Authorization: `Bearer ${this.context.tokens.districtAdmin}` }
      }
    );
    
    if (approvalResponse.status !== 200) {
      throw new Error(`Failed to approve IEP: ${approvalResponse.status}`);
    }
    
    console.log(`  ✅ IEP approved and ready for implementation`);
  }

  private async verifyAdminPortalSummary(): Promise<void> {
    console.log('\n📊 Step 5: Verifying admin portal summary...');
    
    const summaryResponse = await this.context.http.get(
      `${config.services.adminPortal}/summary`,
      {
        headers: { Authorization: `Bearer ${this.context.tokens.districtAdmin}` }
      }
    );
    
    if (summaryResponse.status !== 200) {
      throw new Error(`Failed to get admin portal summary: ${summaryResponse.status}`);
    }
    
    const summary = summaryResponse.data;
    
    // Verify populated cards
    const requiredFields = [
      'totalStudents',
      'activeIEPs', 
      'pendingApprovals',
      'recentEnrollments',
      'districtOverview',
      'usageMetrics'
    ];
    
    for (const field of requiredFields) {
      if (!(field in summary)) {
        throw new Error(`Missing required field in summary: ${field}`);
      }
    }
    
    // Verify our test data appears
    if (summary.totalStudents < 1) {
      throw new Error('Expected at least 1 student in summary');
    }
    
    if (summary.activeIEPs < 1) {
      throw new Error('Expected at least 1 active IEP in summary');
    }
    
    console.log(`  ✅ Admin portal summary populated correctly:`);
    console.log(`    - Students: ${summary.totalStudents}`);
    console.log(`    - Active IEPs: ${summary.activeIEPs}`);
    console.log(`    - Pending Approvals: ${summary.pendingApprovals}`);
    console.log(`    - Recent Enrollments: ${summary.recentEnrollments}`);
  }
}

// Run the verification if this script is executed directly
if (require.main === module) {
  const verifier = new Stage1Verifier();
  verifier.run().catch(error => {
    console.error('Verification failed:', error);
    process.exit(1);
  });
}

export default Stage1Verifier;
