default:
	goto-cc -o main.goto main.c
	-cbmc main.goto --trace --xml-ui > cbmc.xml
	cbmc main.goto --cover location --xml-ui > coverage.xml
	cbmc main.goto --show-properties --xml-ui > property.xml
	cbmc-viewer --goto main.goto --result cbmc.xml --coverage coverage.xml --property property.xml --srcdir .
	diff viewer-trace.json report/json/viewer-trace.json

clean:
	$(RM) -r *~ main.goto cbmc.xml coverage.xml property.xml report
