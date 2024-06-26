"""Add image_filename to Posts model

Revision ID: 9a088c1de1dc
Revises: 391dd8570426
Create Date: 2023-06-17 09:23:40.092872

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a088c1de1dc'
down_revision = '391dd8570426'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_filename', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.drop_column('image_filename')

    # ### end Alembic commands ###
