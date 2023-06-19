"""add foreign key

Revision ID: 3deeffac6322
Revises: fc4b573bd098
Create Date: 2023-06-17 02:54:35.702150

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3deeffac6322'
down_revision = 'fc4b573bd098'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('poster_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_posts_poster_id_users', 'user', ['poster_id'], ['id'])

def downgrade():
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.drop_constraint('fk_posts_poster_id_users', type_='foreignkey')
        batch_op.drop_column('poster_id')