class Config:
func Config.__init_fields(this):
    this.VERSION = "1.0"
    this.activo = true
    this.factor = 2.0
    return
endfunc
endclass
func __main():
    $t1 = new Config
    param $t1
    call Config.__init_fields, 1
    c = $t1
    $t1 = c.VERSION
    print $t1
    $t1 = c.activo
    print $t1
    $t1 = c.factor
    print $t1
endfunc
