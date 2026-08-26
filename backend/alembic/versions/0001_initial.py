"""initial schema

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa
revision='0001_initial'; down_revision=None; branch_labels=None; depends_on=None
def upgrade():
 op.create_table('users',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('email',sa.String(160),unique=True,nullable=False),sa.Column('password_hash',sa.String(255),nullable=False),sa.Column('role',sa.String(30),nullable=False))
 op.create_table('datasets',sa.Column('id',sa.String(36),primary_key=True),sa.Column('name',sa.String(255),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False),sa.Column('normalized',sa.Boolean(),nullable=False),sa.Column('validated',sa.Boolean(),nullable=False))
 op.create_table('loans',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('dataset_id',sa.String(36),sa.ForeignKey('datasets.id'),nullable=False),sa.Column('source_row',sa.Integer(),nullable=False),sa.Column('data',sa.Text(),nullable=False),sa.Column('normalized_data',sa.Text(),nullable=False),sa.Column('record_hash',sa.String(64),nullable=False),sa.Column('verified',sa.Boolean(),nullable=False),sa.Column('updated_at',sa.DateTime(),nullable=False))
 op.create_table('exceptions',sa.Column('id',sa.String(36),primary_key=True),sa.Column('dataset_id',sa.String(36),sa.ForeignKey('datasets.id'),nullable=False),sa.Column('loan_id',sa.Integer(),sa.ForeignKey('loans.id'),nullable=False),sa.Column('field',sa.String(80),nullable=False),sa.Column('rule',sa.String(100),nullable=False),sa.Column('message',sa.Text(),nullable=False),sa.Column('severity',sa.String(15),nullable=False),sa.Column('status',sa.String(20),nullable=False),sa.Column('ai_explanation',sa.Text()),sa.Column('ai_suggestion',sa.Text()),sa.Column('created_at',sa.DateTime(),nullable=False))
 op.create_table('audits',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('dataset_id',sa.String(36),nullable=False),sa.Column('loan_id',sa.Integer()),sa.Column('event',sa.String(100),nullable=False),sa.Column('actor',sa.String(160),nullable=False),sa.Column('detail',sa.Text(),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False))
def downgrade():
 op.drop_table('audits');op.drop_table('exceptions');op.drop_table('loans');op.drop_table('datasets');op.drop_table('users')
