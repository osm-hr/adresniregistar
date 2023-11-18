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
            Sve kolone imaju jedan od tri znaka - „✅”, „⚠️️” ili „❌”. Ovi znaci znače:
            <ul>
                <li>✅ &mdash; Sve je u redu sa ovim tagom</li>
                <li>⚠️️ &mdash; Tag ne postoji. U nastavku je <s>precrtano</s> napisano šta mislimo da bi trebalo da stoji za vrednost ovog taga</li>
                <li>❌ &mdash; Tag postoji, ali mislimo da je pogrešan. U nastavku su navedene trenutna vrednost taga i (posle strelice) šta bi trebalo da bude vrednost tog taga</li>
            </ul>
            Semantika kolona je sledeća:
            <ul>
			<li><b>OSM id</b> &mdash; ID ulice u OSM-u</li>
			<li><b>„ref:RS:ulica” tag</b> &mdash; Označava samo da li postoji „ref:RS:ulica” tag ili ne. Zgodno je za filtriranje</li>
			<li><b>„name” tag</b> &mdash; Stanje „name” taga. Ovaj tag može da bude pogrešan samo ukoliko postoji „ref:RS:ulica” tag, pa je onda pogrešan u odnosu na RGZ. <b>PAŽNJA:</b> moguće je da je ime dobro, a da je zapravo pogrešan „ref:RS:ulica” tag</li>
			<li><b>„name:sr” tag</b> &mdash; Stanje „name:sr” taga. Ukoliko postoji „ref:RS:ulica” tag, onda se gleda da li je pogrešan u odnosu na RGZ. Ako ga nema, onda se gleda da li je pogrešan u odnosu na „name” tag</li>
			<li><b>„name:sr-Latn” tag</b> &mdash; Stanje „name:sr-Latn” taga. Ukoliko postoji „ref:RS:ulica” tag, onda se gleda da li je pogrešan u odnosu na RGZ. Ako ga nema, onda se gleda da li je pogrešan u odnosu na „name” tag</li>
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
	  <li class="breadcrumb-item" aria-current="page"><a href="../qa.html">QA</a></li>
      <li class="breadcrumb-item" aria-current="page"><a href="../wrong_names.html">Loši nazivi ulica</a></li>
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
            } else if (errorType === 'no') {
                refExistsFilter = data[1].indexOf('❌') > -1;
            }

            let errorTypeFilter = true;
            if (errorType === 'wrong_name') {
                errorTypeFilter = data[2].indexOf('❌') > -1;
            } else if (errorType === 'missing_name') {
                errorTypeFilter = data[2].indexOf('⚠') > -1;
            } else if (errorType === 'wrong_name_sr') {
                errorTypeFilter = data[3].indexOf('❌') > -1;
            } else if (errorType === 'missing_name_sr') {
                errorTypeFilter = data[3].indexOf('⚠') > -1;
            } else if (errorType === 'wrong_name_sr_latn') {
                errorTypeFilter = data[4].indexOf('❌') > -1;
            } else if (errorType === 'missing_name_sr_latn') {
                errorTypeFilter = data[4].indexOf('⚠') > -1;
            }

			return refExistsFilter && errorTypeFilter;
		});

	    var table = $('#list').DataTable({
		    stateSave: true,
		    order: [[0, 'desc']],
		    lengthMenu: [ [10, 100, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [2], className: 'text-right' },
		    ],
            "columns": [
                null,
                { "width": "5%" },
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

<h2>Loši nazivi ulica</h2>
<br/>
<p>Ovde možete da vidite sve ulice u OpenStreetMap-apa koje na neki način nemaju dobar neki od „name” tagova za opštinu „{{ opstina_name }}”.
    Svaka kolona ima svoje specifično značenje i ovde je natrpano dosta informacija na jednom mestu, pa <b>savetujemo da pročitate <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a></b> u gornjem meniju da bolje razumete kako da tumačite tabelu.
    U gornjem desnom uglu je filtriranje po raznim kriterijumima.
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
      <option value="wrong_name">name pogrešan</option>
      <option value="missing_name">name nedostaje</option>
      <option value="wrong_name_sr">name:sr pogrešan</option>
      <option value="missing_name_sr">name:sr nedostaje</option>
      <option value="wrong_name_sr_latn">name:sr-Latn pogrešan</option>
      <option value="missing_name_sr_latn">name:sr-Latn nedostaje</option>
    </select>
</div>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-75">
<thead class="thead-dark sticky-top">
	<tr>
		<th>OSM id</th>
		<th>„ref:RS:ulica” tag</th>
        <th>„name” tag</th>
        <th>„name:sr” tag</th>
        <th>„name:sr-Latn” tag</th>
	</tr>
</thead>
<tbody>
	{% for street in streets %}
	<tr>
		<td><a href="{{ street.osm_link }}" target="_blank">{{ street.osm_id }}</a></td>
		<td>{% if street.has_ref_rs_ulica %}✅{% else %}❌{% endif %}</td>
        <td>
            {% if street.wrong_name %}
            ❌ {{ street.osm_name }} ➝ {{ street.osm_name_proper }}
            {% elif street.missing_name %}
            ⚠️️ <s>{{ street.osm_name_proper }}</s>
            {% else %}
            ✅ {{ street.osm_name }}
            {% endif %}
        </td>
        <td>
            {% if street.wrong_name_sr %}
            ❌ {{ street.osm_name_sr }} ➝ {{ street.osm_name_sr_proper }}
            {% elif street.missing_name_sr %}
            ⚠️️ <s>{{ street.osm_name_sr_proper }}</s>
            {% else %}
            ✅ {{ street.osm_name_sr }}
            {% endif %}
        </td>
        <td>
            {% if street.wrong_name_sr_latn %}
            ❌ {{ street.osm_name_sr_latn }} ➝ {{ street.osm_name_sr_latn_proper }}
            {% elif street.missing_name_sr_latn %}
            ⚠️ <s>{{ street.osm_name_sr_latn_proper }}</s>
            {% else %}
            ✅ {{ street.osm_name_sr_latn }}
            {% endif %}
        </td>
	</tr>
	{% endfor %}
</tbody>
</table>

{% endblock %}