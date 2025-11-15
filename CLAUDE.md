# AI-DLC and Spec-Driven Development

Kiro-style Spec Driven Development implementation on AI-DLC (AI Development Life Cycle)

## Project Context

### Paths

- Steering: `.kiro/steering/`
- Specs: `.kiro/specs/`

### Steering vs Specification

**Steering** (`.kiro/steering/`) - Guide AI with project-wide rules and context
**Specs** (`.kiro/specs/`) - Formalize development process for individual features

### Active Specifications

- Check `.kiro/specs/` for active specifications
- Use `/kiro:spec-status [feature-name]` to check progress

## Development Guidelines

- Think in English, but generate responses in Japanese (思考は英語、回答の生成は日本語で行うように)

## Code Documentation Constraints

**IMPORTANT**: `.kiro/specs/` はGitHub管理対象外のため、プロダクトコード・コミットメッセージ・PRにspecsへの参照を含めてはならない

### 禁止事項

- ❌ プロダクトコード内のコメントでspecsファイル（requirements.md, design.md等）を参照
- ❌ コミットメッセージでspecsの内容を引用
- ❌ PR説明でspecsファイルへのリンクを記載
- ❌ コード内で「Requirement X.Y」のような仕様書参照

### 推奨事項

- ✅ コメントは実装意図を自己完結的に説明
- ✅ 技術的根拠（AWS公式ドキュメント、ベストプラクティス）を明記
- ✅ セキュリティ要件はAWS Well-Architected Frameworkを参照
- ✅ GitHub Issue番号での追跡は許可（Issue本体はGitHub管理）

## Minimal Workflow

- Phase 0 (optional): `/kiro:steering`, `/kiro:steering-custom`
- Phase 1 (Specification):
  - `/kiro:spec-init "description"`
  - `/kiro:spec-requirements {feature}`
  - `/kiro:validate-gap {feature}` (optional: for existing codebase)
  - `/kiro:spec-design {feature} [-y]`
  - `/kiro:validate-design {feature}` (optional: design review)
  - `/kiro:spec-tasks {feature} [-y]`
- Phase 2 (Implementation): `/kiro:spec-impl {feature} [tasks]`
  - `/kiro:validate-impl {feature}` (optional: after implementation)
- Progress check: `/kiro:spec-status {feature}` (use anytime)

## Development Rules

- 3-phase approval workflow: Requirements → Design → Tasks → Implementation
- Human review required each phase; use `-y` only for intentional fast-track
- Keep steering current and verify alignment with `/kiro:spec-status`

## Steering Configuration

- Load entire `.kiro/steering/` as project memory
- Default files: `product.md`, `tech.md`, `structure.md`
- Custom files are supported (managed via `/kiro:steering-custom`)
