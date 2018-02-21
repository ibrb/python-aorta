from marshmallow import fields
from marshmallow import validate
import marshmallow

from aorta.router.criterion import Criterion
from aorta.router.rule import Rule


class CriterionSchema(marshmallow.Schema):
    attname = fields.String(
        required=True,
        load_from='name'
    )

    op = fields.String(
        required=True,
        validate=[
            validate.OneOf(list(Criterion._matching_ops.keys()))
        ],
        load_from='operator'
    )

    value = fields.Field(
        required=True
    )

    def load(self, *args, **kwargs):
        params, errors = super(CriterionSchema, self).load(*args, **kwargs)
        if errors:
            return params, errors

        return Criterion(**params), errors


class RuleSchema(marshmallow.Schema):
    return_to_sender = fields.Boolean(
        required=False,
        missing=False
    )

    destinations = fields.List(
        fields.Field(),
        required=True
    )

    criterions = fields.List(
        fields.Nested(CriterionSchema),
        required=True,
        validate=[
            validate.Length(min=1)
        ]
    )

    exclude = fields.List(
        fields.String(),
        required=False,
        default=list,
        missing=list
    )

    def load(self, *args, **kwargs):
        params, errors = super(RuleSchema, self).load(*args, **kwargs)
        if errors:
            return params, errors

        return (Rule(**params), errors)\
            if not self.many\
            else ([Rule(**x) for x in params], errors)
