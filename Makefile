############################################
-include Makefile.options
############################################
url?=
work_dir?=data
python_cmd=PYTHONPATH=./ LOG_LEVEL=INFO python
n?=10
############################################
${work_dir}:
	mkdir -p $@	
############################################
install/req:
	# conda create --name tl python=3.10
	pip install -r requirements.txt
############################################
${work_dir}/.done: | ${work_dir}
	$(python_cmd) src/download.py --url $(url) --out_dir ${work_dir} --user ${user} --password ${pass} --domain ${domain} --n ${n}
	touch $@
dwn: ${work_dir}/.done	
############################################
clean:
	rm -rf $(work_dir)
.PHONY: clean

