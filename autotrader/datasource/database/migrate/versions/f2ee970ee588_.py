"""empty message

Revision ID: f2ee970ee588
Revises: 
Create Date: 2019-04-23 16:01:44.100479

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'f2ee970ee588'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('index',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('issue_id', sa.String(length=100), nullable=True),
    sa.Column('feed_quality', sa.String(length=250), nullable=False),
    sa.Column('symbol', sa.String(length=250), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('issue_id'),
    sa.UniqueConstraint('symbol')
    )
    index_to_stock = op.create_table('index_to_stock',
    sa.Column('index_id', sa.Integer(), nullable=True),
    sa.Column('stock_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['index_id'], ['index.id'], ),
    sa.ForeignKeyConstraint(['stock_id'], ['stock.id'], )
    )
    op.alter_column('filter', 'date',
               existing_type=mysql.DATETIME(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               existing_server_default=sa.text('current_timestamp()'))
    op.alter_column('jsondata', 'data',
               existing_type=mysql.LONGTEXT(charset='utf8mb4', collation='utf8mb4_bin'),
               type_=sa.JSON(),
               existing_nullable=True)
    op.alter_column('jsondata', 'date',
               existing_type=mysql.DATETIME(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               existing_server_default=sa.text('current_timestamp()'))
    op.alter_column('orders', 'date',
               existing_type=mysql.DATETIME(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               existing_server_default=sa.text('current_timestamp()'))
    op.alter_column('orders', 'expire_date',
               existing_type=mysql.DATETIME(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
    op.alter_column('orders', 'is_sell',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    op.add_column('series', sa.Column('index_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'series', 'index', ['index_id'], ['id'])
    op.alter_column('signal', 'date',
               existing_type=mysql.DATETIME(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               existing_server_default=sa.text('current_timestamp()'))
    op.alter_column('signal', 'refresh_date',
               existing_type=mysql.DATETIME(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               existing_server_default=sa.text('current_timestamp()'))
    op.add_column('stock', sa.Column('type', sa.String(length=50), nullable=True))
    op.create_unique_constraint(None, 'stock', ['name'])
    op.create_unique_constraint(None, 'stock', ['issue_id'])
    op.drop_constraint('stock_ibfk_2', 'stock', type_='foreignkey')
    # move indices to index table
    con = op.get_bind()
    stock_table = sa.Table('stock', sa.MetaData(bind=con), autoload=True)
    index_table = sa.Table('index', sa.MetaData(bind=con), autoload=True)
    con.execute(
        index_table.insert().from_select(
            ['id', 'symbol', 'feed_quality'],
            sa.select([stock_table.c.id, stock_table.c.symbol, stock_table.c.feed_quality]).where(stock_table.c.is_index)
        )
    )
    # update series indices
    series_table = sa.Table('series', sa.MetaData(bind=con), autoload=True)
    for index in con.execute(sa.select([index_table])):
        con.execute(
            series_table.update().values(index_id=index['id'], stock_id=None).where(series_table.c.stock_id == index['id'])
        )
    # remove duplicate stocks and fill association table
    stock_list = []
    delete_stock_ids = []
    for stock in con.execute(sa.select([stock_table]).where(stock_table.c.is_index == False)):
        if not any(dic['name'] == stock['name'] for dic in stock_list):
            stock_list.append({'name': stock['name'], 'index_ids': [stock['index_id']], 'stock_id': stock['id']})
        else:
            for dic in stock_list:
                if dic['name'] == stock['name']:
                    dic['index_ids'].append(stock['index_id'])
                    delete_stock_ids.append(stock['id'])
    # fill association table
    index_to_stock_data = []
    for stock in stock_list:
        for index in stock['index_ids']:
            index_to_stock_data.append({'stock_id': stock['stock_id'], 'index_id': index})
    op.bulk_insert(index_to_stock, index_to_stock_data)
    # delete duplicate data
    orders_table = sa.Table('orders', sa.MetaData(bind=con), autoload=True)
    parameter_table = sa.Table('parameter', sa.MetaData(bind=con), autoload=True)
    signal_table = sa.Table('signal', sa.MetaData(bind=con), autoload=True)
    filter_table = sa.Table('filter', sa.MetaData(bind=con), autoload=True)
    plot_table = sa.Table('plot', sa.MetaData(bind=con), autoload=True)
    json_table = sa.Table('jsondata', sa.MetaData(bind=con), autoload=True)
    delete_signal_ids = [my_id['id'] for my_id in con.execute(sa.select([signal_table]).where(signal_table.c.stock_id.in_(delete_stock_ids)))]

    con.execute(
        series_table.delete().where(series_table.c.stock_id.in_(delete_stock_ids))
    )

    con.execute(
        series_table.delete().where(series_table.c.resolution == 'PT1S')
    )

    con.execute(
        json_table.delete().where(json_table.c.stock_id.in_(delete_stock_ids))
    )

    con.execute(
        filter_table.delete().where(filter_table.c.stock_id.in_(delete_stock_ids))
    )

    con.execute(
        json_table.delete().where(json_table.c.stock_id.in_(delete_stock_ids))
    )

    con.execute(
        plot_table.delete().where(plot_table.c.signal_id.in_(delete_signal_ids))
    )

    con.execute(
        parameter_table.delete().where(parameter_table.c.signal_id.in_(delete_signal_ids))
    )

    con.execute(
        orders_table.delete().where(orders_table.c.stock_id.in_(delete_stock_ids)).where(orders_table.c.orders_id.isnot(None))
    )

    con.execute(
        orders_table.delete().where(orders_table.c.stock_id.in_(delete_stock_ids))
    )

    con.execute(
        stock_table.delete().where(stock_table.c.id.in_(delete_stock_ids))
    )

    op.drop_column('stock', 'index_id')

    con.execute(
        stock_table.delete().where(stock_table.c.is_index)
    )

    op.drop_column('stock', 'is_index')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('stock', sa.Column('is_index', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.add_column('stock', sa.Column('index_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.create_foreign_key('stock_ibfk_2', 'stock', 'stock', ['index_id'], ['id'])
    op.drop_constraint(None, 'stock', type_='unique')
    op.drop_constraint(None, 'stock', type_='unique')
    op.drop_column('stock', 'type')
    op.alter_column('signal', 'refresh_date',
               existing_type=sa.DateTime(timezone=True),
               type_=mysql.DATETIME(),
               existing_nullable=True,
               existing_server_default=sa.text('current_timestamp()'))
    op.alter_column('signal', 'date',
               existing_type=sa.DateTime(timezone=True),
               type_=mysql.DATETIME(),
               existing_nullable=True,
               existing_server_default=sa.text('current_timestamp()'))
    op.drop_constraint(None, 'series', type_='foreignkey')
    op.alter_column('series', 'volume',
               existing_type=sa.Integer(),
               type_=mysql.BIGINT(display_width=20),
               existing_nullable=True)
    op.drop_column('series', 'index_id')
    op.alter_column('orders', 'is_sell',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('orders', 'expire_date',
               existing_type=sa.DateTime(timezone=True),
               type_=mysql.DATETIME(),
               existing_nullable=True)
    op.alter_column('orders', 'date',
               existing_type=sa.DateTime(timezone=True),
               type_=mysql.DATETIME(),
               existing_nullable=True,
               existing_server_default=sa.text('current_timestamp()'))
    op.alter_column('jsondata', 'date',
               existing_type=sa.DateTime(timezone=True),
               type_=mysql.DATETIME(),
               existing_nullable=True,
               existing_server_default=sa.text('current_timestamp()'))
    op.alter_column('jsondata', 'data',
               existing_type=sa.JSON(),
               type_=mysql.LONGTEXT(charset='utf8mb4', collation='utf8mb4_bin'),
               existing_nullable=True)
    op.alter_column('filter', 'date',
               existing_type=sa.DateTime(timezone=True),
               type_=mysql.DATETIME(),
               existing_nullable=True,
               existing_server_default=sa.text('current_timestamp()'))
    op.drop_table('index_to_stock')
    op.drop_table('index')
    # ### end Alembic commands ###
