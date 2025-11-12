# Personal Algorithmic Trading Platform - Product Requirements Document

**Document Version:** 1.0  
**Last Updated:** November 11, 2025  
**Author:** Piyush (Group Product Manager)  
**Project Code:** ATP-2025

---

## 📋 Document Structure

This PRD is organized into multiple focused documents for better readability and maintenance. Below is the complete document hierarchy:

### Core Documents

1. **[Executive Summary](01_EXECUTIVE_SUMMARY.md)**
   - Project Overview
   - Business Objectives
   - Success Metrics
   - Stakeholders

2. **[SEBI Compliance Requirements](02_COMPLIANCE_REQUIREMENTS.md)**
   - Regulatory Framework (Feb 2025 Circular)
   - Order Per Second Limits (120 OPS for Commodities)
   - Authentication & Security Requirements
   - Audit Trail Specifications
   - Registration Requirements

3. **[Technical Architecture](03_TECHNICAL_ARCHITECTURE.md)**
   - System Architecture Diagram
   - Technology Stack Details
   - Database Schema
   - Infrastructure Setup (GCP Mumbai)
   - Security Architecture

4. **[Feature Specifications](04_FEATURE_SPECIFICATIONS.md)**
   - Strategy Plugin System
   - Backtesting Engine
   - Paper Trading Module
   - Live Trading System
   - Dashboard & UI Components

5. **[Broker Integration & Data Management](05_DATA_MANAGEMENT.md)**
   - Zerodha Kite Connect Integration
   - Groww API Integration
   - Historical Data Management
   - Real-time Data Streaming
   - Rate Limiting Strategy

6. **[Risk Management System](06_RISK_MANAGEMENT.md)**
   - Position Limits
   - Stop Loss Mechanisms
   - Daily Loss Limits
   - Circuit Breakers
   - Kill Switch Implementation

7. **[Implementation Plan](07_IMPLEMENTATION_PLAN.md)**
   - Phase 0: Foundation (Week 1-4)
   - Phase 1: Core Features (Week 5-12)
   - Phase 2: Live Trading (Week 13-16)
   - Phase 3: Enhancement (Post-Launch)

8. **[Testing Strategy](08_TESTING_STRATEGY.md)**
   - Unit Testing Requirements
   - Integration Testing
   - End-to-End Testing
   - Performance Testing
   - Compliance Testing

---

## 🎯 Quick Reference

### Key Information

| Attribute | Details |
|-----------|---------|
| **Platform Type** | Personal Algorithmic Trading Platform |
| **Primary Users** | 2-3 Individual Investors (Self + Family/Friends) |
| **Target Markets** | NSE, BSE (Equity Cash initially, F&O later) |
| **Brokers** | Zerodha Kite Connect, Groww API |
| **Tech Stack** | FastAPI, Celery, Redis, PostgreSQL/TimescaleDB, React/Next.js |
| **Infrastructure** | GCP (Mumbai Region) - Single VM |
| **Starting Capital** | ₹2-3 Lakhs |
| **Target Capacity** | 10 Orders/Second (well below 120 OPS SEBI limit) |
| **Compliance Deadline** | August 1, 2025 (SEBI new regulations effective) |

### Critical Compliance Points

✅ **Mandatory from Day 1:**
- OAuth-based authentication (SEBI requirement)
- Two-factor authentication for API access
- Unique algo identifier tagging for all orders
- Static IP whitelisting
- Complete audit trail for all algo orders
- Order per second tracking and monitoring

✅ **Personal Use Exemption:**
- Registration with Exchange only if crossing OPS threshold (TBD by April 1, 2025)
- White-box algorithms (logic disclosed and replicable)
- No Research Analyst registration required
- Can be used by self + immediate family

---

## 📊 Success Metrics

### Phase 0 (Foundation) - Week 1-4
- [ ] Successful OAuth integration with Zerodha + Groww
- [ ] Basic UI with authentication working
- [ ] Database schema implemented
- [ ] Audit logging operational

### Phase 1 (Core) - Week 5-12
- [ ] 5+ strategies successfully implemented and backtested
- [ ] Backtesting engine processing 1000+ combinations/hour
- [ ] Paper trading running 24/5 without errors
- [ ] Strategy hot-reload working

### Phase 2 (Live Trading) - Week 13-16
- [ ] First live trade executed successfully
- [ ] Risk controls preventing loss beyond limits
- [ ] 99.9% uptime during market hours
- [ ] Zero compliance violations

### Phase 3 (Enhancement) - Post-Launch
- [ ] 10+ strategies running in parallel
- [ ] Portfolio optimization working
- [ ] Multi-timeframe analysis operational
- [ ] F&O trading integrated

---

## 🚀 Getting Started

To understand the complete platform requirements:

1. **Start with** [Executive Summary](01_EXECUTIVE_SUMMARY.md) for high-level understanding
2. **Review** [SEBI Compliance](02_COMPLIANCE_REQUIREMENTS.md) for regulatory context
3. **Study** [Technical Architecture](03_TECHNICAL_ARCHITECTURE.md) for implementation details
4. **Follow** [Implementation Plan](07_IMPLEMENTATION_PLAN.md) for execution roadmap

---

## 📝 Document Conventions

### Priority Levels
- 🔴 **P0 (Critical):** Must have for MVP, regulatory requirement
- 🟡 **P1 (High):** Important for core functionality
- 🟢 **P2 (Medium):** Nice to have, can be deferred
- ⚪ **P3 (Low):** Future enhancement

### Status Indicators
- ✅ Completed
- 🚧 In Progress
- 📋 Planned
- ⏸️ On Hold
- ❌ Blocked

---

## 🔄 Document Version Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Nov 11, 2025 | Piyush | Initial PRD creation |

---

## 📞 Contact & Escalation

**Product Owner:** Piyush  
**Role:** Group Product Manager  
**Experience:** 12+ years (6+ in Product Management)  
**Expertise:** Marketplace dynamics, AI implementation, scalable platforms

---

## ⚠️ Important Notes

1. **SEBI Compliance:** Implementation standards to be finalized by Broker's Industry Standards Forum by April 1, 2025. Monitor for updates.

2. **OPS Threshold:** Current limit is 120 OPS for commodities (rolling 5-second window). Our target of 10 OPS provides 12x safety margin.

3. **Broker API Costs:**
   - Zerodha: ₹2,000/month (API) + ₹2,000/month (Historical Data)
   - Groww: Included in Trading API subscription

4. **Timeline:** Aggressive 16-week timeline to be operational before August 1, 2025 SEBI deadline.

---

## 📚 Additional Resources

- [Zerodha Kite Connect API Documentation](https://kite.trade/docs/connect/v3/)
- [Groww Trade API Documentation](https://groww.in/trade-api/docs/python-sdk)
- [SEBI Circular - Retail Algo Trading (Feb 4, 2025)](https://www.sebi.gov.in)
- [SEBI Circular - OPS Limits (Mar 17, 2022)](https://www.sebi.gov.in)

---

**Next Steps:**
1. Review all linked documents
2. Set up development environment
3. Begin Phase 0 implementation
4. Schedule weekly progress reviews

---

*This is a living document. Updates will be made as requirements evolve and SEBI guidelines are clarified.*
