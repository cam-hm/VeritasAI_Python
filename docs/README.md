# Design Documentation

Tài liệu thiết kế và đặc tả cho RAG ChatApp SAAS MVP.

## 📚 Tài liệu

### 1. FEATURE_DESIGN.md
Thiết kế tính năng đầy đủ cho hệ thống SAAS, bao gồm:
- User personas & use cases
- Core features (3 phases)
- Technical architecture
- Database schema
- API design
- Security & compliance
- Pricing & monetization

### 2. MVP_PREPARATION.md
Checklist và hướng dẫn chuẩn bị trước khi code MVP:
- Pre-development checklist
- Database design requirements
- API design requirements
- Testing strategy
- Development environment setup

### 3. DATABASE_SCHEMA_MVP.md
Thiết kế database schema chi tiết cho MVP:
- Multi-tenant models (Organization, OrganizationMember)
- Core models (Document, Chatbot, ChatSession, etc.)
- Relationships và indexes
- Migration strategy
- Data isolation strategy

### 4. API_SPECIFICATION_MVP.md
Đặc tả API endpoints cho MVP:
- Authentication endpoints
- Organization management
- Document management
- Chatbot management
- Chat endpoints
- API keys
- Error handling
- Rate limiting

### 5. TECHNICAL_DECISIONS_MVP.md
Ghi lại các quyết định kỹ thuật quan trọng:
- Multi-tenant strategy
- Authentication strategy
- File storage strategy
- Background job processing
- Vector search strategy
- LLM provider strategy
- Frontend strategy
- Testing strategy

### 6. PROTOTYPE_TO_SAAS_MIGRATION.md
Kế hoạch migration từ prototype sang SAAS MVP:
- Current state analysis
- Migration strategy
- Code reusability analysis
- Action plan

## 🎯 Cách sử dụng

Khi coding, luôn tham khảo các tài liệu này để:
- ✅ Đảm bảo đúng architecture
- ✅ Follow database schema design
- ✅ Implement đúng API specification
- ✅ Tuân thủ technical decisions
- ✅ Maintain consistency

## 📝 Lưu ý

- Các tài liệu này là **living documents** - sẽ được update khi có thay đổi
- Trước khi implement feature mới, review relevant documentation
- Nếu có conflict giữa code và documentation, update documentation

