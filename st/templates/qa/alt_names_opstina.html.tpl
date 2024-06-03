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
            <br>
            <ul>
                <li>Ukoliko „alt_name” ima simbol „✅”, znači da je sve u redu sa ovim tagom.</li>
                <li>Ukoliko „alt_name” ima simbol „⚠️”, znači da ovaj tag nedostaje.
                    <s>Precrtano</s> je navedeno kako algoritam kaže da tag treba da izgleda.
                    Ukoliko ima deo sa kurzivom opkružen zvezdicama, to znači da se ovaj deo imena ulice samo nagađa</li>
                <li>Ukoliko „alt_name” ima simbol „❌️”, znači da ovaj tag postoji, ali heuristika misli da nije ispravan-.
                    U nastavku je navedeno trenutna vrednosti i koju vrednost algoritam misli da treba da bude.
                    Ukoliko ima deo sa kurzivom opkružen zvezdicama, to znači da se ovaj deo imena ulice samo nagađa</li>
            </ul>
            Kolone u tabeli:
            <ul>
                <li><b>OSM</b> &mdash; Link ka OSM ulici i ime ulice u OSM-u</li>
                <li><b>„ref:RS:ulica” tag</b> &mdash; Označava da li je ulica spojena sa RGZ-om preko „ref:RS:ulica” taga. Ukoliko jeste, prikaza je simbol „✅” i identifikator ulice u RGZ-u</li>
                <li><b>RGZ ime</b> &mdash; Ukoliko je OSM ulica spojena sa RGZ-om, ovde je navedeno ime ulice u RGZ-u</li>
                <li><b>„name” tag</b> &mdash; Vrednost „name” taga iz OSM-a. Navedena su i RGZ i OSM imena, čisto da čovek može da ih proveri oba</li>
                <li><b>„alt_name” tag</b> &mdash; Stanje „alt_name” taga na osnovu algoritma. Pogledajte iznad kako da tumačite ovu kolonu</li>
                <li><b>„alt_name:sr” tag</b> &mdash; Stanje „alt_name:sr” taga na osnovu algoritma. Pogledajte iznad kako da tumačite ovu kolonu</li>
                <li><b>„alt_name:sr-Latn” tag</b> &mdash; Stanje „alt_name:sr-Latn” taga na osnovu algoritma. Pogledajte iznad kako da tumačite ovu kolonu</li>
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
    <li class="breadcrumb-item" aria-current="page"><a href="../../index.html">DINA</a></li>
    <li class="breadcrumb-item" aria-current="page"><a href="../index.html">Ulice</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="../qa.html">QA</a></li>
    <li class="breadcrumb-item" aria-current="page"><a href="../alt_names.html">Alternativni nazivi ulica</a></li>
    <li class="breadcrumb-item" aria-current="page">{{ opstina_name }}</li>
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
		$.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
		    let refExists = $("#refExistsSelect option:selected").val();
			let errorType = $("#errorTypeSelect option:selected").val();

            let refExistsFilter = true;
            if (refExists === 'yes') {
                refExistsFilter = data[1].indexOf('✅') > -1;
            } else if (refExists === 'no') {
                refExistsFilter = data[1].indexOf('❌') > -1;
            }

            let errorTypeFilter = true;
            if (errorType === 'all_wrong_alt_names') {
                errorTypeFilter = data[4].indexOf('❌') > -1 || data[5].indexOf('❌') > -1 || data[6].indexOf('❌') > -1;
            } else if (errorType === 'all_missing_alt_names') {
                errorTypeFilter = data[4].indexOf('⚠') > -1 || data[5].indexOf('⚠') > -1 || data[6].indexOf('⚠') > -1;
            } else if (errorType === 'wrong_alt_name') {
                errorTypeFilter = data[4].indexOf('❌') > -1;
            } else if (errorType === 'missing_alt_name') {
                errorTypeFilter = data[4].indexOf('⚠') > -1;
            } else if (errorType === 'wrong_alt_name_sr') {
                errorTypeFilter = data[5].indexOf('❌') > -1;
            } else if (errorType === 'missing_alt_name_sr') {
                errorTypeFilter = data[5].indexOf('⚠') > -1;
            } else if (errorType === 'wrong_alt_name_sr_latn') {
                errorTypeFilter = data[6].indexOf('❌') > -1;
            } else if (errorType === 'missing_alt_name_sr_latn') {
                errorTypeFilter = data[6].indexOf('⚠') > -1;
            }

			return refExistsFilter && errorTypeFilter;
		});

	    var table = $('#list').DataTable({
		    stateSave: true,
		    stateDuration: 0,
			stateSaveCallback: function (settings, data) {
				localStorage.setItem('DataTables_st_alt_naselje', JSON.stringify(data));
			},
			stateLoadCallback: function (settings) {
				return JSON.parse(localStorage.getItem('DataTables_st_alt_naselje'));
			},
		    order: [[0, 'desc']],
		    lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		    columnDefs: [
		    ],
            "columns": [
                null,
                { "width": "10%" },
                null,
                null,
                null,
                null,
                null
              ]
		});

        $('#refExistsSelect').on('change', function() {
            table.draw();
        });
        $('#errorTypeSelect').on('change', function() {
            table.draw();
        });
	} );
    </script>

<h2>Alternativni nazivi ulica</h2>
<br/>
<p>Ovde možete da vidite potencijalne probleme sa „alt_name” tagom za ulice u OpenStreetMap-apa za opštinu „{{ opstina_name }}”. Moguće je da „alt_name” tag fali, a moguće je i da je pogrešan.
    <br/>
    Savetujemo da pročitate <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a> u gornjem meniju da bolje razumete kako da tumačite tabelu.
    U gornjem desnom uglu je filtriranje.
</p>
<br/>
<br/>

<div class="text-right">
    <label for="errorType">Postoji ref:RS:ulica tag:</label>
    <select name="refExists" id="refExistsSelect">
      <option value="all"></option>
      <option value="yes">Da</option>
      <option value="no">Ne</option>
    </select>
    <br/>
    <label for="errorType">Tip greške:</label>
    <select name="errorType" id="errorTypeSelect">
      <option value="all">Sve</option>
      <option value="all_wrong_alt_names">Svi pogrešni tagovi</option>
      <option value="all_missing_alt_names">Samo nedostajući tagovi</option>
      <option disabled>-</option>
      <option value="wrong_alt_name">Pogrešan „alt_name” tag</option>
      <option value="missing_alt_name">Nedostajući „alt_name” tag</option>
      <option value="wrong_alt_name_sr">Pogrešan „alt_name:sr” tag</option>
      <option value="missing_alt_name_sr">Nedostajući „alt_name:sr” tag</option>
      <option value="wrong_alt_name_sr_latn">Pogrešan „alt_name:sr-Latn” tag</option>
      <option value="missing_alt_name_sr_latn">Nedostajući „alt_name:sr-Latn” tag</option>
    </select>
</div>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-100">
<thead class="thead-dark sticky-top">
	<tr>
		<th>OSM id</th>
		<th>„ref:RS:ulica” tag</th>
		<th>RGZ ime (OSM „name” tag)</th>
        <th>„name” tag</th>
        <th>„alt_name” tag</th>
        <th>„alt_name:sr” tag</th>
        <th>„alt_name:sr-Latn” tag</th>
	</tr>
</thead>
<tbody>
	{% for street in streets %}
	<tr>
		<td><a href="{{ street.osm_link }}" target="_blank">{{ street.osm_name }}</a></td>
		<td>{% if street.has_ref_rs_ulica %}✅ {{ street.ref_rs_ulica }}{% else %}❌{% endif %}</td>
		<td>{% if street.rgz_ulica_proper != '' %}{{ street.rgz_ulica_proper }}{% else %}❌{% endif %}</td>
		<td>{% if street.osm_name != '' %}{{ street.osm_name }}{% else %}❌{% endif %}</td>
        <td>
            {% if street.is_missing_alt_name %}
            ⚠️ <s>{{ street.alt_name_suggestion|safe }}</s>
            {% elif street.is_wrong_alt_name %}
            ❌ „{{ street.osm_alt_name }}” ➔ „{{ street.alt_name_suggestion|safe }}”
            {% else %}
            ✅ {{ street.osm_alt_name }}
            {% endif %}
        </td>
        <td>
            {% if street.is_missing_alt_name_sr %}
            ⚠️ <s>{{ street.alt_name_sr_suggestion|safe }}</s>
            {% elif street.is_wrong_alt_name_sr %}
            ❌ „{{ street.osm_alt_name_sr }}” ➔ „{{ street.alt_name_sr_suggestion|safe }}”
            {% else %}
            ✅ {{ street.osm_alt_name_sr }}
            {% endif %}
        </td>
        <td>
            {% if street.is_missing_alt_name_sr_latn %}
            ⚠️ <s>{{ street.alt_name_sr_latn_suggestion|safe }}</s>
            {% elif street.is_wrong_alt_name_sr_latn %}
            ❌ „{{ street.osm_alt_name_sr_latn }}” ➔ „{{ street.alt_name_sr_latn_suggestion|safe }}”
            {% else %}
            ✅ {{ street.osm_alt_name_sr_latn }}
            {% endif %}
        </td>
	</tr>
	{% endfor %}
</tbody>
</table>

{% endblock %}