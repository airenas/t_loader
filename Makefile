############################################
-include Makefile.options
############################################
url?=
work_dir?=data
python_cmd=PYTHONPATH=./ LOG_LEVEL=INFO python
n?=10
version?=0.1
final_file=$(CURDIR)/nta-$(version)-$(shell date +'%y-%m-%d_%H-%M').zip
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
############################################
$(final_file): $(work_dir)/.done $(work_dir)/info.txt
	cd $(work_dir); zip -r $@ *
zip: $(final_file)	
	echo "Final file is: $(final_file)"
############################################
$(work_dir)/info.txt: $(work_dir)/.done
	@printf "NTA texts\n----------------\n" > $@
	@printf "version     : $(version)\n" >> $@
	@printf "prepared at : `date +'%Y-%m-%d %H:%M:%S'`\n" >> $@
	@printf "total files : `ls $(work_dir)/*.xml | wc -l`\n" >> $@
	@printf "total size  : `ls $(work_dir)/*.xml | xargs du -sch | tail -1 | cut -f1`\n" >> $@

############################################
clean:
	rm -rf $(work_dir)
.PHONY: clean

