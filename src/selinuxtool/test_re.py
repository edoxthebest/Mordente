import re

raw_string = """--BEGIN--
/(vendor|system/vendor)/lib(64)?/liblzma\\.so		u:object_r:same_process_hal_file:s0
@NFA-explicit
%Alphabet-auto
%Initial q0
%Final q25
q0 47 q1
q1 115 q2
q29 109 q30
q30 47 q31
q31 118 q3
--END--
--BEGIN--
/(vendor|system/vendor)/lib(64)?/libblas\\.so		u:object_r:same_process_hal_file:s0
@NFA-explicit
%Alphabet-auto
%Initial q0
%Final q25
q0 47 q1
q1 115 q2
q1 118 q3
q2 121 q26
q3 101 q4
q4 110 q5
q18 98 q19
q19 108 q20
q30 47 q31
q31 118 q3
--END--
--BEGIN--
/(vendor|system/vendor)/lib(64)?/libbase\\.so		u:object_r:same_process_hal_file:s0
@NFA-explicit
%Alphabet-auto
%Initial q0
%Final q25
q0 47 q1
q1 115 q2
q1 118 q3
q2 121 q26
q3 101 q4
q4 110 q5
--END--
"""

ctx_expr = re.compile(r'^--BEGIN--\n([^\s]*)\t([^\s]*)\t([^\s]*)\n(.*?)\n--END--$', re.DOTALL | re.MULTILINE)
print(ctx_expr.findall(raw_string))