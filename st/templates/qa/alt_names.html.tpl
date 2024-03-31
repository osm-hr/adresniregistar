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
        Ovaj izveštaj proverava da li ime ulice treba da ima pridružen „alt_name” tag. Ime ulice se uzima iz RGZ-a ako postoji
        (ako je way spojen preko „ref:RS:ulica” taga), a ako ne postoji - uzima se „name”/„name:sr”/„name:sr-Latn” tag.
        Heuristika proverava da li ime ulice sadrži broj (ili kao arapske cifre, ili kao napisane brojeve), ili reč "doktor" i pokušava
        da pogodi koji bi „alt_name” tag trebao da bude (ovo su jedine provere za sad).
        Zbog specifičnosti srpskog jezika (rodovi, padeži i sl.), nekad ne može da se odredi kako bi „alt_name” trebalo da izgleda,
        ali može da se posumnja da nije dobro specificiran.
        <br><br>
        Kolone u tabeli:
		<ul>
			<li><b>Opština</b> &mdash; Opština analize</li>
			<li><b># Pogrešan „alt_name”</b> &mdash; Ukupan broj adresa gde „alt_name” tag postoji, ali heuristika sumnja da nije pravilno napisan. Ne znači da je „alt_name” pogrešan, možda je i „name” tag pogrešan, a možda i algoritam greši!</li>
			<li><b># Nedostaje „alt_name”</b> &mdash; Ukupan broj adresa gde heuristika kaže da „alt_name” tag treba da postoji, ali nije nađen</li>
			<li><b># Pogrešan „alt_name:sr”</b> &mdash; Ukupan broj adresa gde „alt_name:sr” tag postoji, ali heuristika sumnja da nije pravilno napisan. Ne znači da je „alt_name:sr” pogrešan, možda je i „name:sr” tag pogrešan, a možda i algoritam greši!</li>
			<li><b># Nedostaje „alt_name:sr”</b> &mdash; Ukupan broj adresa gde heuristika kaže da „alt_name:sr” tag treba da postoji, ali nije nađen</li>
			<li><b># Pogrešan „alt_name:sr-Latn”</b> &mdash; Ukupan broj adresa gde „alt_name:sr-Latn” tag postoji, ali heuristika sumnja da nije pravilno napisan. Ne znači da je „alt_name:sr-Latn” pogrešan, možda je i „name:sr-Latn” tag pogrešan, a možda i algoritam greši!</li>
			<li><b># Nedostaje „alt_name:sr-Latn”</b> &mdash; Ukupan broj adresa gde heuristika kaže da „alt_name:sr-Latn” tag treba da postoji, ali nije nađen</li>
		</ul>
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
	<li class="breadcrumb-item" aria-current="page"><a href="qa.html">QA</a></li>
	<li class="breadcrumb-item" aria-current="page">Alternativni nazivi</li>
  </ol>
</nav>
    <!-- Optional JavaScript -->
    <!-- jQuery first, then Popper.js, then Bootstrap JS -->
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.18/js/jquery.dataTables.min.js" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.18/js/dataTables.bootstrap4.min.js" crossorigin="anonymous"></script>
    <script>
	$(document).ready( function () {
	    $('#list').DataTable({
		    stateSave: true,
		    order: [[0, 'asc']],
		    lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [1, 2, 3, 4, 5, 6], className: 'text-right' },
		    ]
		});
	} );
    </script>

<h2>Alternativni nazivi ulica</h2>
<br/>
<p>Ovde možete da vidite potencijalne probleme sa „alt_name” tagom za ulice u OpenStreetMap-apa. Moguće je da neka verzija „alt_name” taga fali, a moguće je i da je pogrešna.
    Klikom na opštinu dobijate detaljnije podatke za tu opštinu. U gornjem desnom uglu je filtriranje.
    <br/>
    <br/>
    Da biste bolje razumeli značenje kolona u tabeli, pogledajte <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a>.
    <br/>
    <br/>
    <b>Pažljivo prilikom otvaranja opština preko 5.000 adresa, računar i browser mogu da se uspore znatno!</b>
</p>
<br/>
<br/>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-50">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Opština</th>
		<th># Pogrešan „alt_name”</th>
		<th># Nedostaje „alt_name”</th>
		<th># Pogrešan „alt_name:sr”</th>
		<th># Nedostaje „alt_name:sr”</th>
		<th># Pogrešan „alt_name:sr-Latn”</th>
		<th># Nedostaje „alt_name:sr-Latn”</th>
	</tr>
</thead>
<tbody>
	{% for opstina in opstine %}
	<tr>
		<td><a href="alt_names/{{ opstina.name }}.html">{{ opstina.name }}</a></td>
		<td>{{ opstina.wrong_alt_name }}</td>
		<td>{{ opstina.missing_alt_name }}</td>
		<td>{{ opstina.wrong_alt_name_sr }}</td>
		<td>{{ opstina.missing_alt_name_sr }}</td>
		<td>{{ opstina.wrong_alt_name_sr_latn }}</td>
		<td>{{ opstina.missing_alt_name_sr_latn }}</td>
	</tr>
	{% endfor %}
</tbody>
<tfoot>
	<tr>
		<th>Serbia TOTAL:</th>
		<th class="d-sm-table-cell">{{ total.wrong_alt_name }}</th>
		<th class="d-sm-table-cell">{{ total.missing_alt_name }}</th>
		<th class="d-sm-table-cell">{{ total.wrong_alt_name_sr }}</th>
		<th class="d-sm-table-cell">{{ total.missing_alt_name_sr }}</th>
		<th class="d-sm-table-cell">{{ total.wrong_alt_name_sr_latn }}</th>
		<th class="d-sm-table-cell">{{ total.missing_alt_name_sr_latn }}</th>
	</tr>
</tfoot>
</table>

{% endblock %}