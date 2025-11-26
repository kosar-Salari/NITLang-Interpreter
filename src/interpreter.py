from token_types import TokenType
from ast_nodes import (
    Number, BinaryOp, Identifier, FunctionDef,
    FunctionCall, IfExpr, Comparison, LetStatement,
    LetExpression, Block, RefExpr, DerefExpr, RefAssign,
    BoolLiteral, StringLiteral,
    FieldDef, ClassDef, NewExpr, MemberAccess, MethodCall, Assign
)


# =========================================
#            Cell for Mutable Memory
# =========================================
class Cell:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Cell({self.value})"


# =========================================
#            Instance for OO
# =========================================
class Instance:
    def __init__(self, class_def):
        self.class_def = class_def
        self.fields = {}  # name -> Cell

    def __repr__(self):
        field_repr = {k: v for k, v in self.fields.items()}
        return f"<Instance {self.class_def.name} {field_repr}>"


# =========================================
#            Environment
# =========================================
class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.functions = {}
        self.variables = {}  # name -> Cell
        self.classes = {}    # name -> ClassDef

    def define_function(self, name, func_def):
        self.functions[name] = func_def

    def get_function(self, name):
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.get_function(name)
        raise Exception(f"Undefined function: {name}")

    def define_class(self, name, class_def):
        self.classes[name] = class_def

    def get_class(self, name):
        if name in self.classes:
            return self.classes[name]
        if self.parent:
            return self.parent.get_class(name)
        raise Exception(f"Undefined class: {name}")

    def define_variable(self, name, value):
        # اگر value از قبل Cell بود (مثل ref x)، دوباره wrap نکن
        if isinstance(value, Cell):
            self.variables[name] = value
        else:
            self.variables[name] = Cell(value)

    def get_cell(self, name):
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get_cell(name)
        raise Exception(f"Undefined variable: {name}")

    def __repr__(self):
        return f"Env(vars={self.variables}, funcs={list(self.functions.keys())}, classes={list(self.classes.keys())})"


# =========================================
#            Interpreter
# =========================================
class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.current_env = self.global_env

    # ------------- dispatch -------------
    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        raise Exception(f'No visit_{type(node).__name__} method')

    # ------------- helpers -------------
    def _unwrap(self, v):
        if isinstance(v, Cell):
            return v.value
        return v

    def _type_name(self, v):
        if isinstance(v, Cell):
            v = v.value
        if isinstance(v, bool):
            return "bool"
        if isinstance(v, int):
            return "int"
        if isinstance(v, str):
            return "string"
        if isinstance(v, Instance):
            return v.class_def.name
        return "unknown"

    def default_value_for_type(self, tname):
        if tname == "int":
            return 0
        if tname == "bool":
            return False
        if tname == "string":
            return ""
        return None

    def check_type(self, annotation, value):
        if annotation is None:
            return
        actual = self._type_name(value)
        if actual != annotation:
            raise Exception(f"Type error: expected {annotation}, got {actual}")

    # -------------------------
    # Literals & Identifiers
    # -------------------------
    def visit_Number(self, node):
        return node.value

    def visit_BoolLiteral(self, node):
        return node.value

    def visit_StringLiteral(self, node):
        return node.value

    def visit_Identifier(self, node):
        name = node.name
        # اول سعی کن متغیر معمولی پیدا کنی
        try:
            return self.current_env.get_cell(name)
        except Exception:
            # اگر self داریم و instance است، تلاش کن از فیلدهای self بخونی
            try:
                self_cell = self.current_env.get_cell("self")
            except Exception:
                raise Exception(f"Undefined variable: {name}")

            inst = self._unwrap(self_cell)
            if isinstance(inst, Instance) and name in inst.fields:
                return inst.fields[name]

            raise Exception(f"Undefined variable or field: {name}")

    # -------------------------
    # Arithmetic
    # -------------------------
    def visit_BinaryOp(self, node):
        left_val = self._unwrap(self.visit(node.left))
        right_val = self._unwrap(self.visit(node.right))

        # فقط int مجاز است (نه bool)
        if type(left_val) is not int:
            raise Exception(f"Type error in arithmetic: left operand is {self._type_name(left_val)}")
        if type(right_val) is not int:
            raise Exception(f"Type error in arithmetic: right operand is {self._type_name(right_val)}")

        if node.operator == TokenType.PLUS:
            return left_val + right_val
        elif node.operator == TokenType.MINUS:
            return left_val - right_val
        elif node.operator == TokenType.MULTIPLY:
            return left_val * right_val
        elif node.operator == TokenType.DIVIDE:
            if right_val == 0:
                raise Exception("Division by zero")
            return left_val // right_val

        raise Exception(f"Unknown binary operator: {node.operator}")

    # -------------------------
    # Comparison
    # -------------------------
    def visit_Comparison(self, node):
        left_val = self._unwrap(self.visit(node.left))
        right_val = self._unwrap(self.visit(node.right))

        if type(left_val) is not type(right_val):
            raise Exception(
                f"Type error in comparison: cannot compare "
                f"{self._type_name(left_val)} with {self._type_name(right_val)}"
            )

        if node.operator == TokenType.EQUALS:
            return 1 if left_val == right_val else 0

        raise Exception(f"Unknown comparison operator: {node.operator}")

    # -------------------------
    # If expression
    # -------------------------
    def visit_IfExpr(self, node):
        condition_val = self._unwrap(self.visit(node.condition))

        if isinstance(condition_val, bool):
            cond = condition_val
        elif isinstance(condition_val, int):
            cond = (condition_val != 0)
        else:
            raise Exception(
                f"Type error in if condition: expected bool or int, got {self._type_name(condition_val)}"
            )

        if cond:
            return self.visit(node.true_branch)
        else:
            return self.visit(node.false_branch)

    # -------------------------
    # Let
    # -------------------------
    def visit_LetStatement(self, node: LetStatement):
        value = self.visit(node.value)
        self.check_type(node.type_annotation, value)
        self.current_env.define_variable(node.name, value)
        return f"Variable '{node.name}' = {self._unwrap(value)}"

    def visit_LetExpression(self, node: LetExpression):
        value = self.visit(node.value)
        self.check_type(node.type_annotation, value)

        new_env = Environment(parent=self.current_env)
        new_env.define_variable(node.name, value)

        previous_env = self.current_env
        self.current_env = new_env
        try:
            result = self.visit(node.body)
            return result
        finally:
            self.current_env = previous_env

    # -------------------------
    # Function definition
    # -------------------------
    def visit_FunctionDef(self, node):
        self.global_env.define_function(node.name, node)
        return f"Function '{node.name}' defined"

    # -------------------------
    # Function call (global)
    # -------------------------
    def visit_FunctionCall(self, node):
        func_def = self.global_env.get_function(node.name)
        arg_values = [self.visit(arg) for arg in node.arguments]

        if len(arg_values) != len(func_def.params):
            raise Exception(
                f"Function '{node.name}' expects {len(func_def.params)} "
                f"arguments, got {len(arg_values)}"
            )

        func_env = Environment(parent=self.global_env)

        for param_name, arg_value in zip(func_def.params, arg_values):
            func_env.define_variable(param_name, arg_value)

        previous_env = self.current_env
        self.current_env = func_env

        try:
            result = self.visit(func_def.body)
            return result
        finally:
            self.current_env = previous_env

    # -------------------------
    # Block
    # -------------------------
    def visit_Block(self, node):
        last = None
        for stmt in node.statements:
            last = self.visit(stmt)
        return last

    # ====================================================
    #                  MEMORY: ref, deref, :=
    # ====================================================
    def visit_RefExpr(self, node):
        return self.current_env.get_cell(node.identifier.name)

    def visit_DerefExpr(self, node):
        cell = self.current_env.get_cell(node.identifier.name)
        return cell.value

    def visit_RefAssign(self, node):
        cell = self.visit(node.ref)
        if not isinstance(cell, Cell):
            raise Exception("Ref assignment target is not a reference (Cell)")

        old_value = cell.value
        new_value = self._unwrap(self.visit(node.value))

        if type(old_value) is not type(new_value):
            raise Exception(
                f"Type error: expected {self._type_name(old_value)}, got {self._type_name(new_value)}"
            )

        cell.value = new_value
        return new_value

    # ====================================================
    #                  CLASSES / OBJECTS
    # ====================================================
    def visit_ClassDef(self, node: ClassDef):
        self.global_env.define_class(node.name, node)
        return f"Class '{node.name}' defined"

    def _find_method(self, class_def, name):
        for m in class_def.methods:
            if m.name == name:
                return m
        return None

    def _find_field_def(self, class_def, field_name):
        for f in class_def.fields:
            if f.name == field_name:
                return f
        return None

    def visit_NewExpr(self, node: NewExpr):
        class_def = self.global_env.get_class(node.class_name)
        inst = Instance(class_def)

        # مقداردهی اولیه‌ی فیلدها
        for field in class_def.fields:
            default = self.default_value_for_type(field.type_annotation)
            inst.fields[field.name] = Cell(default)

        # constructor شبیه init
        init_method = self._find_method(class_def, "init")
        if init_method:
            arg_values = [self.visit(a) for a in node.arguments]
            if len(arg_values) != len(init_method.params):
                raise Exception(
                    f"Constructor for {class_def.name} expects {len(init_method.params)} "
                    f"arguments, got {len(arg_values)}"
                )

            method_env = Environment(parent=self.global_env)
            method_env.define_variable("self", inst)
            for pname, pval in zip(init_method.params, arg_values):
                method_env.define_variable(pname, pval)

            prev_env = self.current_env
            self.current_env = method_env
            try:
                self.visit(init_method.body)
            finally:
                self.current_env = prev_env
        else:
            if node.arguments:
                raise Exception(
                    f"Class {class_def.name} has no init method but arguments were provided"
                )

        return inst

    def visit_MemberAccess(self, node: MemberAccess):
        obj_val = self._unwrap(self.visit(node.obj))
        if not isinstance(obj_val, Instance):
            raise Exception("Member access on non-object value")

        if node.member_name not in obj_val.fields:
            raise Exception(f"Unknown field '{node.member_name}' on {obj_val.class_def.name}")

        return obj_val.fields[node.member_name]

    def visit_MethodCall(self, node: MethodCall):
        obj_val = self._unwrap(self.visit(node.obj))
        if not isinstance(obj_val, Instance):
            raise Exception("Method call on non-object value")

        class_def = obj_val.class_def
        method_def = self._find_method(class_def, node.method_name)
        if not method_def:
            raise Exception(f"Undefined method '{node.method_name}' for class {class_def.name}")

        arg_values = [self.visit(a) for a in node.arguments]
        if len(arg_values) != len(method_def.params):
            raise Exception(
                f"Method '{node.method_name}' expects {len(method_def.params)} "
                f"arguments, got {len(arg_values)}"
            )

        method_env = Environment(parent=self.global_env)
        method_env.define_variable("self", obj_val)
        for pname, pval in zip(method_def.params, arg_values):
            method_env.define_variable(pname, pval)

        prev_env = self.current_env
        self.current_env = method_env
        try:
            result = self.visit(method_def.body)
            return result
        finally:
            self.current_env = prev_env

    # -------------------------
    # Assignment (x = expr, obj.f = expr)
    # -------------------------
    def visit_Assign(self, node: Assign):
        value = self._unwrap(self.visit(node.value))

        # Identifier assignment (لوکال یا فیلدِ self)
        if isinstance(node.target, Identifier):
            name = node.target.name
            # اول تلاش برای متغیر عادی
            try:
                cell = self.current_env.get_cell(name)
                old_value = cell.value
                if type(old_value) is not type(value):
                    raise Exception(
                        f"Type error: expected {self._type_name(old_value)}, "
                        f"got {self._type_name(value)}"
                    )
                cell.value = value
                return value
            except Exception:
                # اگر self داریم و field باشد
                try:
                    self_cell = self.current_env.get_cell("self")
                except Exception:
                    raise Exception(f"Undefined variable: {name}")

                inst = self._unwrap(self_cell)
                if not isinstance(inst, Instance):
                    raise Exception(f"Undefined variable: {name}")

                if name not in inst.fields:
                    raise Exception(f"Unknown field '{name}' on {inst.class_def.name}")

                field_def = self._find_field_def(inst.class_def, name)
                if field_def and field_def.type_annotation:
                    expected = field_def.type_annotation
                    actual = self._type_name(value)
                    if expected != actual:
                        raise Exception(
                            f"Type error: field {name} of {inst.class_def.name} "
                            f"expects {expected}, got {actual}"
                        )

                inst.fields[name].value = value
                return value

        # MemberAccess assignment: obj.field = expr
        if isinstance(node.target, MemberAccess):
            obj_val = self._unwrap(self.visit(node.target.obj))
            if not isinstance(obj_val, Instance):
                raise Exception("Member assignment on non-object value")

            field_name = node.target.member_name
            if field_name not in obj_val.fields:
                raise Exception(f"Unknown field '{field_name}' on {obj_val.class_def.name}")

            field_def = self._find_field_def(obj_val.class_def, field_name)
            if field_def and field_def.type_annotation:
                expected = field_def.type_annotation
                actual = self._type_name(value)
                if expected != actual:
                    raise Exception(
                        f"Type error: field {field_name} of {obj_val.class_def.name} "
                        f"expects {expected}, got {actual}"
                    )

            obj_val.fields[field_name].value = value
            return value

        raise Exception("Invalid assignment target")

    # -------------------------
    # main interpret
    # -------------------------
    def interpret(self, tree):
        result = self.visit(tree)
        if isinstance(result, Cell):
            return result.value
        return result
