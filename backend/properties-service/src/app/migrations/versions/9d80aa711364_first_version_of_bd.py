"""First version of bd

Revision ID: 9d80aa711364
Revises:
Create Date: 2026-04-27 12:50:53.315432

"""
from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9d80aa711364'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('properties',
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('updated_by', sa.Uuid(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_by', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('property_type', sa.Enum('house', 'apartment', name='propertytype'), nullable=False),
    sa.Column('listing_type', sa.Enum('sale', 'rent', name='listingtype'), nullable=False),
    sa.Column('condition', sa.Enum('new', 'used', name='propertycondition'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'active', 'inactive', 'sold', 'rented', name='listingstatus'), nullable=False),
    sa.Column('currency', sa.Enum('COP', 'USD', 'EUR', 'MXN', 'PEN', 'CLP', 'ARS', name='currency'), nullable=False),
    sa.Column('verification_status', sa.Enum('unverified', 'pending', 'verified', 'rejected', name='verificationstatus'), nullable=False),
    sa.Column('verified_by', sa.Uuid(), nullable=True),
    sa.Column('rejection_reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('floor_number', sa.Integer(), nullable=True),
    sa.Column('total_floors', sa.Integer(), nullable=True),
    sa.Column('area_m2', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('bedrooms', sa.Integer(), nullable=False),
    sa.Column('bathrooms', sa.Numeric(precision=3, scale=1), nullable=False),
    sa.Column('parking_spots', sa.Integer(), nullable=False),
    sa.Column('h3_r9', sqlmodel.sql.sqltypes.AutoString(length=16), nullable=True),
    sa.Column('h3_r7', sqlmodel.sql.sqltypes.AutoString(length=16), nullable=True),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('year_built', sa.Integer(), nullable=True),
    sa.Column('admin_fee', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('stratum', sa.Integer(), nullable=True),
    sa.Column('price', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('admin_estimated_price', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('admin_estimated_price_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ml_estimated_price', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('ml_estimated_price_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("property_type != 'apartment' OR floor_number IS NOT NULL", name='ck_apartment_floor_number_required'),
    sa.CheckConstraint("property_type != 'house' OR total_floors IS NOT NULL", name='ck_house_total_floors_required'),
    sa.CheckConstraint('area_m2 > 0', name='ck_property_area_m2_positive'),
    sa.CheckConstraint('bathrooms >= 1', name='ck_property_bathrooms_min_one'),
    sa.CheckConstraint('bedrooms > 0', name='ck_property_bedrooms_positive'),
    sa.CheckConstraint('price > 0', name='ck_property_price_positive'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_properties_h3_r7'), 'properties', ['h3_r7'], unique=False)
    op.create_index(op.f('ix_properties_h3_r9'), 'properties', ['h3_r9'], unique=False)
    op.create_index(op.f('ix_properties_id'), 'properties', ['id'], unique=False)
    op.create_index(op.f('ix_properties_owner_id'), 'properties', ['owner_id'], unique=False)
    op.create_index('ix_properties_owner_id_status', 'properties', ['owner_id', 'status'], unique=False)
    op.create_index('ix_properties_price', 'properties', ['price'], unique=False)
    op.create_index('ix_properties_status', 'properties', ['status'], unique=False)
    op.create_table('promoted_listings',
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('updated_by', sa.Uuid(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_by', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('property_id', sa.Uuid(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.CheckConstraint('ends_at > starts_at', name='ck_promoted_listing_ends_after_starts'),
    sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_promoted_listings_id'), 'promoted_listings', ['id'], unique=False)
    op.create_index(op.f('ix_promoted_listings_property_id'), 'promoted_listings', ['property_id'], unique=False)
    op.create_index('ix_promoted_listings_property_id_ends_at', 'promoted_listings', ['property_id', 'ends_at'], unique=False)
    op.create_table('property_image_upload_batches',
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('updated_by', sa.Uuid(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_by', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('property_id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'ready', 'confirmed', 'expired', 'failed', name='batchstatus'), nullable=False),
    sa.Column('expected_keys', sa.ARRAY(sa.Text()), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_property_image_upload_batches_id'), 'property_image_upload_batches', ['id'], unique=False)
    op.create_index('ix_upload_batches_owner_id', 'property_image_upload_batches', ['owner_id'], unique=False)
    op.create_index('ix_upload_batches_property_id', 'property_image_upload_batches', ['property_id'], unique=False)
    op.create_table('property_images',
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('updated_by', sa.Uuid(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_by', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('property_id', sa.Uuid(), nullable=False),
    sa.Column('url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('status', sa.Enum('active', 'pending_delete', 'deleted', name='imagestatus'), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('is_cover', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_property_images_id'), 'property_images', ['id'], unique=False)
    op.create_index(op.f('ix_property_images_property_id'), 'property_images', ['property_id'], unique=False)
    op.create_index('ix_property_images_property_id_status', 'property_images', ['property_id', 'status'], unique=False)
    op.create_index('ix_property_images_url', 'property_images', ['url'], unique=True)
    op.create_index('uix_property_images_cover', 'property_images', ['property_id'], unique=True, postgresql_where=sa.text("is_cover = true AND status = 'active'"))
    op.create_table('property_locations',
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('updated_by', sa.Uuid(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_by', sa.Uuid(), nullable=True),
    sa.Column('property_id', sa.Uuid(), nullable=False),
    sa.Column('neighborhood_id', sa.Uuid(), nullable=False),
    sa.Column('city_id', sa.Uuid(), nullable=False),
    sa.Column('country_id', sa.Uuid(), nullable=False),
    sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('property_id')
    )
    op.create_index('ix_property_locations_city_id', 'property_locations', ['city_id'], unique=False)
    op.create_index('ix_property_locations_country_id', 'property_locations', ['country_id'], unique=False)
    op.create_index('ix_property_locations_gist', 'property_locations', ['location'], unique=False, postgresql_using='gist')
    op.create_index('ix_property_locations_neighborhood_id', 'property_locations', ['neighborhood_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_property_locations_neighborhood_id', table_name='property_locations')
    op.drop_index('ix_property_locations_gist', table_name='property_locations', postgresql_using='gist')
    op.drop_index('ix_property_locations_country_id', table_name='property_locations')
    op.drop_index('ix_property_locations_city_id', table_name='property_locations')
    op.drop_table('property_locations')
    op.drop_index('uix_property_images_cover', table_name='property_images', postgresql_where=sa.text("is_cover = true AND status = 'active'"))
    op.drop_index('ix_property_images_url', table_name='property_images')
    op.drop_index('ix_property_images_property_id_status', table_name='property_images')
    op.drop_index(op.f('ix_property_images_property_id'), table_name='property_images')
    op.drop_index(op.f('ix_property_images_id'), table_name='property_images')
    op.drop_table('property_images')
    op.drop_index('ix_upload_batches_property_id', table_name='property_image_upload_batches')
    op.drop_index('ix_upload_batches_owner_id', table_name='property_image_upload_batches')
    op.drop_index(op.f('ix_property_image_upload_batches_id'), table_name='property_image_upload_batches')
    op.drop_table('property_image_upload_batches')
    op.drop_index('ix_promoted_listings_property_id_ends_at', table_name='promoted_listings')
    op.drop_index(op.f('ix_promoted_listings_property_id'), table_name='promoted_listings')
    op.drop_index(op.f('ix_promoted_listings_id'), table_name='promoted_listings')
    op.drop_table('promoted_listings')
    op.drop_index('ix_properties_status', table_name='properties')
    op.drop_index('ix_properties_price', table_name='properties')
    op.drop_index('ix_properties_owner_id_status', table_name='properties')
    op.drop_index(op.f('ix_properties_owner_id'), table_name='properties')
    op.drop_index(op.f('ix_properties_id'), table_name='properties')
    op.drop_index(op.f('ix_properties_h3_r9'), table_name='properties')
    op.drop_index(op.f('ix_properties_h3_r7'), table_name='properties')
    op.drop_table('properties')
