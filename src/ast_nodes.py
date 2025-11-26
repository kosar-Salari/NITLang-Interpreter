class ASTNode:
    pass


class Number(ASTNode):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Number({self.value})"


class BoolLiteral(ASTNode):
    def __init__(self, value: bool):
        self.value = value

    def __repr__(self):
        return f"Bool({self.value})"


class StringLiteral(ASTNode):
    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f"String({self.value!r})"


class BinaryOp(ASTNode):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right


class RefExpr(ASTNode):
    def __init__(self, identifier):
        self.identifier = identifier


class DerefExpr(ASTNode):
    def __init__(self, identifier):
        self.identifier = identifier


class RefAssign(ASTNode):
    def __init__(self, ref, value):
        self.ref = ref
        self.value = value

    def __repr__(self):
        return f"RefAssign({self.ref} := {self.value})"


class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Identifier({self.name})"


class FunctionDef(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

    def __repr__(self):
        params_str = ', '.join(self.params)
        return f"FunctionDef({self.name}({params_str}) = {self.body})"


class FunctionCall(ASTNode):
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

    def __repr__(self):
        args_str = ', '.join(str(arg) for arg in self.arguments)
        return f"FunctionCall({self.name}({args_str}))"


class IfExpr(ASTNode):
    def __init__(self, condition, true_branch, false_branch):
        self.condition = condition
        self.true_branch = true_branch
        self.false_branch = false_branch

    def __repr__(self):
        return f"IfExpr(if {self.condition} then {self.true_branch} else {self.false_branch})"


class Comparison(ASTNode):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"Comparison({self.left} {self.operator.name} {self.right})"


class LetStatement(ASTNode):
    def __init__(self, name, type_annotation, value):
        self.name = name
        self.type_annotation = type_annotation  # "int", "bool", "string" or None
        self.value = value

    def __repr__(self):
        if self.type_annotation:
            return f"LetStatement({self.name}:{self.type_annotation} = {self.value})"
        return f"LetStatement({self.name} = {self.value})"


class LetExpression(ASTNode):
    def __init__(self, name, type_annotation, value, body):
        self.name = name
        self.type_annotation = type_annotation  # "int", "bool", "string" or None
        self.value = value
        self.body = body

    def __repr__(self):
        if self.type_annotation:
            return f"LetExpression(let {self.name}:{self.type_annotation} = {self.value} in {self.body})"
        return f"LetExpression(let {self.name} = {self.value} in {self.body})"


class Block(ASTNode):
    def __init__(self, statements):
        self.statements = statements

    def __repr__(self):
        return f"Block({self.statements})"


# -----------------------------
# Object Orientation (Step 6)
# -----------------------------
class FieldDef(ASTNode):
    def __init__(self, name, type_annotation):
        self.name = name
        self.type_annotation = type_annotation  # "int", "bool", "string" or None

    def __repr__(self):
        return f"FieldDef({self.name}:{self.type_annotation})"


class ClassDef(ASTNode):
    def __init__(self, name, fields, methods):
        self.name = name
        self.fields = fields      # list[FieldDef]
        self.methods = methods    # list[FunctionDef]

    def __repr__(self):
        return f"ClassDef({self.name}, fields={self.fields}, methods={self.methods})"


class NewExpr(ASTNode):
    def __init__(self, class_name, arguments):
        self.class_name = class_name
        self.arguments = arguments

    def __repr__(self):
        args_str = ', '.join(str(a) for a in self.arguments)
        return f"New({self.class_name}({args_str}))"


class MemberAccess(ASTNode):
    def __init__(self, obj, member_name):
        self.obj = obj
        self.member_name = member_name

    def __repr__(self):
        return f"MemberAccess({self.obj}.{self.member_name})"


class MethodCall(ASTNode):
    def __init__(self, obj, method_name, arguments):
        self.obj = obj
        self.method_name = method_name
        self.arguments = arguments

    def __repr__(self):
        args_str = ', '.join(str(a) for a in self.arguments)
        return f"MethodCall({self.obj}.{self.method_name}({args_str}))"


class Assign(ASTNode):
    def __init__(self, target, value):
        self.target = target   # Identifier یا MemberAccess
        self.value = value

    def __repr__(self):
        return f"Assign({self.target} = {self.value})"
