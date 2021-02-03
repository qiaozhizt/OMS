# -*- coding: utf-8 -*-


BASE_CHOICES = (
    ('', ''),
    ('IN', 'In'),
    ('OUT', 'Out'),
    ('UP', 'Up'),
    ('DOWN', 'Down')
)

PRODUCT_TYPE_CHOICES = (
    ('FRAME', 'Frame'),
    ('LENS', 'Lens'),
    ('TINT', 'Tint'),
    ('COATING', 'Coating'),
    ('CLIPON', 'Clipon'),
    ('ACCESSORIES', 'Accessories'),
    ('PRISM', 'Prism'),
)

USED_FOR_CHOICES = (
    ('', 'NULL'),
    ('PROGRESSIVE', 'Progressive'),
    ('DISTANCE', 'Distance'),
    ('READING', 'Reading')
)

PRESCRIPTION_CHOICES = (
    ('', 'NULL'),
    ('N', 'Plano'),
    ('S', 'Single Vision'),
    ('P', 'Progressive')
)

LENS_COLOR_CHOICES = (
    ('', 'NULL'),
    ('G', 'Gray'),
    ('B', 'Brown'),
    ('E', 'Green'),
    ('I', 'Pink'),
    ('Y', 'Yellow'),
)

VENDOR_CHOICES = (
    ('0', '0'),
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5'),
    ('6', '6'),
    ('7', '7'),
    ('8', '8'),
    ('9', '9'),
    ('10', '10'),
    ('11', '11'),
    ('12', '12'),
    ('13', '13'),
    ('14', '14'),
    ('15', '15'),
    ('1000', '1000-Frame Only')
)

LENS_INDEX_CHOICES = (
    ('1.50', '1.50'),
    ('1.56', '1.56'),
    ('1.59', '1.59'),
    ('1.61', '1.61'),
    ('1.67', '1.67'),
    ('1.71', '1.71'),
    ('1.74', '1.74'),
)

IDENTIFICATION_CHOICES = (
    ('R', 'Right'),
    ('L', 'Left'),
)

LENS_TYPE_CHOICES = (
    ('0', 'Single Vision'),
    ('1', 'Progressive'),
    ('2', 'Bifocal'),
)

