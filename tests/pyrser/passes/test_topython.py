import ast
import collections
import unittest

from pyrser import codegen
from pyrser import parsing
from pyrser import passes
from pyrser.passes import topython


#Immutable stub ParseTree node
ParseTreeStub = collections.namedtuple('ParseTreeStub', 'name inline')


def visit_ParseTreeStub(self, node: ParseTreeStub) -> [ast.stmt] or ast.expr:
    """Function to generate expression for stub ParseTree nodes."""
    expr = ast.Name(node.name, ast.Load())
    return expr if node.inline else self._clause(expr)


#TODO(bps): Fix brittle test suite by testing behavior instead of code
class TestToPythonPasse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        topython.RuleVisitor.visit_ParseTreeStub = visit_ParseTreeStub

    @classmethod
    def tearDownClass(self):
        del topython.RuleVisitor.visit_ParseTreeStub

    def test_topython_generates_code_for_call(self):
        method = parsing.BasicParser.readChar
        call = parsing.Call(method, 'a')
        res = codegen.to_source(passes.rule_topython(call))
        self.assertEqual(res, "self.readChar('a')")

    def test_topython_generates_code_for_calltrue(self):
        method = parsing.BasicParser.readChar
        call = parsing.CallTrue(method, 'a')
        res = codegen.to_source(passes.rule_topython(call))
        self.assertEqual(res, "lambda : (self.readChar('a') or True)")

    def test_topython_generates_code_for_hook(self):
        parser = None
        hook = parsing.Hook('hookname', tuple())
        res = codegen.to_source(passes.rule_topython(hook))
        self.assertEqual(res,
                         "self.evalHook('hookname', self.ruleNodes[(-1)])")

    def test_topython_generates_code_for_rule(self):
        parser = None
        rule = parsing.Rule('rulename')
        res = codegen.to_source(passes.rule_topython(rule))
        self.assertEqual(res, "self.evalRule('rulename')")

    def test_topython_inline_inlinable_clauses(self):
        parser = None
        clauses = parsing.Clauses(
            ParseTreeStub('a', True), ParseTreeStub('b', True))
        res = codegen.to_source(ast.Module(passes.rule_topython(clauses)))
        self.assertEqual(res, "(a and b)")

    def test_topython_generates_code_for_clauses(self):
        parser = None
        clauses = parsing.Clauses(
            ParseTreeStub('a', False), ParseTreeStub('b', False))
        res = codegen.to_source(ast.Module(passes.rule_topython(clauses)))
        self.assertEqual(res, ("if (not a):\n"
                               "    return False\n"
                               "if (not b):\n"
                               "    return False"))

    def test_topython_generates_code_for_complex_clauses(self):
        parser = None
        clauses = parsing.Clauses(
            ParseTreeStub('a', False),
            parsing.Clauses(ParseTreeStub('b', False)))
        res = codegen.to_source(ast.Module(passes.rule_topython(clauses)))
        self.assertEqual(res, ("if (not a):\n"
                               "    return False\n"
                               "if (not b):\n"
                               "    return False"))

    def test_topython_generates_code_for_alt(self):
        parser = None
        alt = parsing.Alt(
            ParseTreeStub('a', False), ParseTreeStub('b', False))
        res = codegen.to_source(ast.Module(passes.rule_topython(alt)))
        self.assertEqual(res, ("try:\n"
                               "    try:\n"
                               "        if (not a):\n"
                               "            raise AltFalse()\n"
                               "        raise AltTrue()\n"
                               "    except AltFalse:\n"
                               "        pass\n"
                               "    try:\n"
                               "        if (not b):\n"
                               "            raise AltFalse()\n"
                               "        raise AltTrue()\n"
                               "    except AltFalse:\n"
                               "        pass\n"
                               "    return False\n"
                               "except AltTrue:\n"
                               "    pass"))

    def test_topython_generates_code_for_complex_alt(self):
        self.maxDiff = None
        parser = None
        alt = parsing.Alt(
            ParseTreeStub('a', False),
            parsing.Clauses(
                ParseTreeStub('b', False),
                parsing.Alt(
                    ParseTreeStub('c', False),
                    ParseTreeStub('d', False))))
        res = codegen.to_source(ast.Module(passes.rule_topython(alt)))
        self.assertEqual(res, ("try:\n"
                               "    try:\n"
                               "        if (not a):\n"
                               "            raise AltFalse()\n"
                               "        raise AltTrue()\n"
                               "    except AltFalse:\n"
                               "        pass\n"
                               "    try:\n"
                               "        if (not b):\n"
                               "            raise AltFalse()\n"
                               "        try:\n"
                               "            try:\n"
                               "                if (not c):\n"
                               "                    raise AltFalse()\n"
                               "                raise AltTrue()\n"
                               "            except AltFalse:\n"
                               "                pass\n"
                               "            try:\n"
                               "                if (not d):\n"
                               "                    raise AltFalse()\n"
                               "                raise AltTrue()\n"
                               "            except AltFalse:\n"
                               "                pass\n"
                               "            raise AltFalse()\n"
                               "        except AltTrue:\n"
                               "            pass\n"
                               "        raise AltTrue()\n"
                               "    except AltFalse:\n"
                               "        pass\n"
                               "    return False\n"
                               "except AltTrue:\n"
                               "    pass"))

    def test_topython_generates_code_for_inlined_repoptional(self):
        rep = parsing.RepOptional(ParseTreeStub('a', True))
        res = codegen.to_source(passes.rule_topython(rep))
        self.assertEqual(res, "(a or True)")

    def test_topython_generates_code_for_repoptional(self):
        rep = parsing.RepOptional(ParseTreeStub('a', False))
        ast_ = ast.Module(passes.rule_topython(rep))
        res = codegen.to_source(ast_)
        self.assertEqual(res, "if (not a):\n"
                              "    pass")

    def test_topython_generates_code_for_rep0n(self):
        parser = None
        rep = parsing.Rep0N(ParseTreeStub('a', False))
        ast_ = ast.Module(passes.rule_topython(rep))
        res = codegen.to_source(ast_)
        self.assertEqual(
            res,
            ("while True:\n"
             "    if (not a):\n"
             "        break"))

    def test_topython_generates_code_for_rep1n(self):
        parser = None
        rep = parsing.Rep1N(ParseTreeStub('a', False))
        res = codegen.to_source(ast.Module(passes.rule_topython(rep)))
        self.assertEqual(
            res,
            ("if (not a):\n"
             "    return False\n"
             "while True:\n"
             "    if (not a):\n"
             "        break"))

#TODO(bps): Finish testing all nodes
#    def test_topython_generates_code_for_capture(self):
#    def test_topython_generates_code_for_scope(self):

#TODO(bps): remove till end of file
    def help(self, rule):
        res = passes.rule_topython(rule)
        stmts = str(res)
        if isinstance(res, list):
            res = ast.Module(res)
        code = codegen.to_source(res)
        return '\n'.join([
            "========= RULE ==========",
            rule.dumpParseTree(),
            "========== AST ==========",
            stmts,
            "========= CODE ==========",
            code,
            "========== END =========="])

    def test_topython_generates_code_for_parserdsl(self):
        from pprint import pprint
        from pyrser.dsl import Parser
        import pyrser.passes.dumpParseTree

        res, parser = [], Parser()
        #res.append(self.help(parser._rules['alternatives']))
        res.append(codegen.to_source(
            passes.parserrule_topython(parser, 'bnf_dsl')))
        res.append(codegen.to_source(
            passes.parserrule_topython(parser, 'rule')))
        res.append(codegen.to_source(
            passes.parserrule_topython(parser, 'alternatives')))
        res.append(codegen.to_source(
            passes.parserrule_topython(parser, 'clauses')))
        res.append(codegen.to_source(
            passes.parserrule_topython(parser, 'clause')))
        res.append(codegen.to_source(
            passes.parserrule_topython(parser, 'rule_name')))
        #print('\n\n'.join(res))
