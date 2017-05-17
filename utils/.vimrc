set autoindent
set tabstop=4
set softtabstop=4
set shiftwidth=4
set smarttab
set expandtab
colors desert
syntax on
set background=dark
set ignorecase
set smartcase
set hlsearch
set incsearch
set nowrap
set listchars+=precedes:<,extends:>
set sidescroll=5
set sidescrolloff=5
set guifont=terminus

" автодополнение фигурной скобки (так, как я люблю :)
imap {<CR> {<CR>}<Esc>O<Tab>
"imap <C-LEFT> <ESC>bi
nmap <M-d> i#doom_changed <ESC> :read !date <CR><UP>J
imap <M-d> #doom_changed <ESC>:read !date <CR><UP>J
"nmap <S-TAB> 0d4l$
"nmap <TAB> 0i<TAB><ESC>$
" автодополнение по Control+Space
imap <C-Space> <C-N>

" 'умный' Home
nmap <Home> ^
imap <Home> <Esc>I

" выход без сохранения
imap <C-F10> <Esc>:q!<CR>
nmap <C-F10> :q!<CR>

" выход с сохранением
imap <F10> <Esc>:wq<CR>
nmap <F10> :wq<CR>

" сохранение текущего буфера
imap <F2> <Esc>:w<CR>a
nmap <F2> :w<CR>

" сохранение всех буферов
"imap <S-F2> <Esc>:wa<CR>a
"nmap <S-F2> :wa<CR>

" список буферов
"imap <S-F4> <Esc>:buffers<CR>
"nmap <S-F4> :buffers<CR>

" закрыть буфер
imap <F4> <Esc>:bd<CR>a
nmap <F4> :bd<CR>

" открыть буфер
imap <F3> <Esc>:e<Space>
nmap <F3> :e<Space>

" следующий буфер
imap <F6> <Esc>:bn!<CR>a
nmap <F6> :bn!<CR>

" предыдущий буфер
imap <F5> <Esc>:bp!<CR>a
nmap <F5> :bp!<CR>

"создать вкладку 
imap <F9> <Esc>:tabnew<CR>a
nmap <F9> :tabnew<CR>

"закрыть вкладку 
"imap <S-tab>c <Esc>:tabc<CR>a
"nmap <S-tab>c :tabc<CR>

"Следующая вкладка
imap <F8> <Esc>:tabnext<CR>a
nmap <F8> :tabnext<CR>
"Предыдущая вкладка
imap <F7> <Esc>:tabprev<CR>a
nmap <F7> :tabprev<CR>

"Разбить экран
imap <C-F9> <Esc>:!./%
nmap <C-F9> <Esc>:!./%
imap <A-F9> <Esc><C-W>s
nmap <A-F9> <Esc><C-W>s

"Сместить экран
imap <C-up> <Esc><C-W>4+
nmap <C-up> <C-W>4+
imap <C-down> <Esc><C-W>4-
nmap <C-down> <C-W>4-
imap <C-left> <Esc><C-W>4<
nmap <C-left> <C-W>4<
imap <C-right> <Esc><C-W>4>
nmap <C-right> <C-W>4>


"Навигация  
imap <M-down> <Esc><C-W>j
nmap <M-down> <C-W>j
imap <M-up> <Esc><C-W>k
nmap <M-up> <C-W>k
imap <M-left> <Esc><C-W>h
nmap <M-left> <C-W>h
imap <M-right> <Esc><C-W>l
nmap <M-right> <C-W>l

" вкл/выкл отображения номеров строк
imap <F12> <Esc>:set<Space>nu!<CR>a
nmap <F12> :set<Space>nu!<CR>
