############################################
-include Makefile.options
############################################
url?=
work_dir?=data
python_cmd=PYTHONPATH=./ LOG_LEVEL=INFO python
n?=10
version?=0.1
final_file=$(CURDIR)/nta-$(version)-$(shell date +'%y-%m-%d_%H-%M').zip
courts_done_files=$(patsubst %,$(work_dir)/corpus/%/.done, $(courts))
top?=0
############################################
${work_dir}:
	mkdir -p $@	
############################################
install/req:
	# conda create --name tl python=3.10
	pip install -r requirements.txt
############################################
${work_dir}/.done: $(courts_done_files) | ${work_dir}
	touch $@
${work_dir}/corpus/%/.done: | ${work_dir}
	$(python_cmd) src/download.py --url $(url) --out_dir ${work_dir} --user ${user} --password ${pass} --domain ${domain} --n ${n} \
		--court $* --top $(top)
	touch $@
dwn: ${work_dir}/.done	
############################################
############################################
$(final_file): $(work_dir)/.done $(work_dir)/corpus/info.txt
	cd $(work_dir)/corpus; zip -r $@ *
zip: $(final_file)	
	echo "Final file is: $(final_file)"
############################################
debug:
	echo "$(courts)"
	echo "$(courts_done_files)"
############################################
$(work_dir)/corpus/info.txt: $(work_dir)/.done
	@printf "NTA texts\n----------------\n" > $@
	@printf "version     : $(version)\n" >> $@
	@printf "prepared at : `date +'%Y-%m-%d %H:%M:%S'`\n" >> $@
	@printf "total files : `find $(work_dir)/corpus -name "*.xml" | wc -l`\n" >> $@
	@printf "total size  : `du -sh $(work_dir)/corpus | cut -f1`\n" >> $@

############################################
clean:
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	rm -rf $(work_dir)
.PHONY: clean
############################################
clean/done:
	find  $(work_dir) -name .done | xargs rm
.PHONY: clean
