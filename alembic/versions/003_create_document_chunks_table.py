"""create document_chunks table

Revision ID: 003
Revises: 002
Create Date: 2025-01-27

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Tạo document_chunks table với pgvector
    Tương đương với create_document_chunks_table migration trong Laravel
    
    Lưu ý: Cần enable pgvector extension trong PostgreSQL trước:
    CREATE EXTENSION IF NOT EXISTS vector;
    """
    # Enable pgvector extension (nếu chưa có)
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(768), nullable=True),  # 768 dimensions cho nomic-embed-text
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_chunks_id'), 'document_chunks', ['id'], unique=False)
    
    # Tạo index cho vector similarity search (tương đương với IVFFlat index trong Laravel)
    # Lưu ý: Cần có data trước khi tạo IVFFlat index
    # op.execute("""
    #     CREATE INDEX document_chunks_embedding_idx ON document_chunks 
    #     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    # """)


def downgrade() -> None:
    op.drop_index(op.f('ix_document_chunks_id'), table_name='document_chunks')
    op.drop_table('document_chunks')

