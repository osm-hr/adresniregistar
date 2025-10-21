{% extends "base.html.tpl" %}
{% block body %}

<!-- Modal -->
<div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="exampleModalLabel">Značenje kolona</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
		Odaberite neku od dostupnih analiza ispod
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">Zatvori</button>
      </div>
    </div>
  </div>
</div>

<nav aria-label="breadcrumb">
  <ol class="breadcrumb">
    <li class="breadcrumb-item" aria-current="page"><a href="../index.html">DINA</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="index.html">Ulice</a></li>
    <li class="breadcrumb-item" aria-current="page">QA</li>
  </ol>
</nav>

<!-- Optional JavaScript -->
<!-- jQuery first, then Popper.js, then Bootstrap JS -->
<script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
<script src="https://cdn.datatables.net/1.10.18/js/jquery.dataTables.min.js" crossorigin="anonymous"></script>
<script src="https://cdn.datatables.net/1.10.18/js/dataTables.bootstrap4.min.js" crossorigin="anonymous"></script>

<div class="text-center">

    <h2>Quality assurance</h2>
    <br/>
    <p>Ovde možete videti neke od QA izveštaja</p>
    <br/>
    <h3>Geometrijski QA</h3>
    <br/>
    <h3><a href="name_mismatch.html">Neslaganje imena</a></h3>
    <p>Pronalazi nepovezane segmente OSM ulica koji se preklapaju sa RGZ geometrijama, a imaju pogrešna imena.</p>
    <h3><a href="geom_missing.html">Nedostajuće geometrije</a></h3>
    <p>Pronalazi greške između RGZ i OSM geometrija</p>
    <br/><br/>
    <h3>Jezički QA</h3>
    <br/>
    <h3><a href="wrong_names.html">Loši nazivi ulica</a></h3>
    <p>Pronalazi OSM ulice kojima se tagovi imena ne slažu sa pravilima imenovanja ulica u Srbiji.</p>
    <h3><a href="alt_names.html">Alternativni nazivi ulica</a></h3>
    <p>Pronalazi OSM ulice kojima se tagovi alt imena ne slažu sa pravilima imenovanja ulica u Srbiji.</p>
    <h3><a href="en_names.html">Engleski nazivi ulica</a></h3>
    <p>Pronalazi OSM ulice kojima je „name:en” tag nepotreban ili potencijalno pogrešan.</p>
    <h3><a href="int_names.html">Int nazivi ulica</a></h3>
    <p>Pronalazi OSM ulice kojima „int_name” tag nedostaje ili je pogrešan</p>
</div>

{% endblock %}
