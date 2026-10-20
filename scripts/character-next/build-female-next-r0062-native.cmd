@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x64
if errorlevel 1 exit /b %errorlevel%
pushd "D:\Download\Aevrynd\Evidence\character-female-next\r0062-packed-bundle\native"
cl /nologo /std:c++20 /EHsc /O2 /MT /LD /fp:strict "D:\Download\Aevrynd\engine\character\physics\shaft_contacts.cpp" /Fo"shaft_contacts.obj" /Fe"aevrynd_shaft_contacts.dll" /link /INCREMENTAL:NO /IMPLIB:"aevrynd_shaft_contacts.lib"
set aevrynd_build_result=%errorlevel%
popd
exit /b %aevrynd_build_result%
