
.PHONY: install

install:
	mkdir -p $(DESTDIR)/usr/share/altcenter/plugins
	cp -a plugins/*.py $(DESTDIR)/usr/share/altcenter/plugins
	mkdir -p $(DESTDIR)/usr/share/altcenter/translations
	cp -a translations/*.md $(DESTDIR)/usr/share/altcenter/translations
	cp -a *.py $(DESTDIR)/usr/share/altcenter
	install -Dp basealt.png $(DESTDIR)/usr/share/altcenter/basealt.png
	cp altcenter_ru.qm $(DESTDIR)/usr/share/altcenter
	install -Dpm0755 altcenter $(DESTDIR)/usr/bin/altcenter
	install -Dpm0644 altcenter.desktop $(DESTDIR)/usr/share/applications/altcenter.desktop
