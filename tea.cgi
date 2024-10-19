#!/usr/bin/perl 

# flat file for genes is not on cronjob.  this machine probably does not have tazendra access, copied from .204  2016 03 24
#
# integrated different dictionary and text for phenotype and go terms.  2017 02 09
#
# filter user input genes by wbgene and display all user inputs with them.  2018 07 20
#
# allow a qvalue threshold for users to limit the highest q value of terms returned.  2019 09 06
#
# get header and footer from caltech curation prod instead of tazendra.  then convert the .css link to a static
# version on caltech curation prod.  this might eventually break, if wormbase changes the name of the file, and
# a cronjob updates the header.  2024 10 18


use CGI;
use strict;
use LWP::Simple;
use LWP::UserAgent;
use Time::HiRes qw( time );

my $startTime = time; my $prevTime = time;
$startTime =~ s/(\....).*$/$1/;
$prevTime  =~ s/(\....).*$/$1/;

# use DBI;
# my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb;host=131.215.52.76", "", "") or die "Cannot connect to database!\n";     # for remote access
# # my $dbh = DBI->connect ( "dbi:Pg:dbname=wobrdb", "", "") or die "Cannot connect to database!\n";
# my $result;

my $query = new CGI;
my $base_solr_url = 'http://localhost:8080/solr/';		# raymond dev URL 2015 07 24

my ($infogif) = &getInfoGif();

my $datatypeLabel = 'Tissue';
my ($var, $datatype)  = &getHtmlVar($query, 'datatype');
unless ($datatype) { $datatype = 'anatomy'; }
# if ($datatype eq 'anatomy')             { $datatypeLabel = 'Tissue'; }
#   elsif ($datatype eq 'phenotype')      { $datatypeLabel = 'Phenotype'; }
#   elsif ($datatype eq 'go')             { $datatypeLabel = 'Gene Ontology'; }
#   elsif ($datatype eq 'go_component')   { $datatypeLabel = 'Gene Ontology - Cellular Component'; }
#   elsif ($datatype eq 'go_function')    { $datatypeLabel = 'Gene Ontology - Molecular Function'; }
#   elsif ($datatype eq 'go_process')     { $datatypeLabel = 'Gene Ontology - Biological Process'; }
# $datatypeLabel = qq( Tissue + Anatomy + GO );
# my $title = $datatypeLabel . ' Enrichment Analysis';
my $title = 'Enrichment Analysis';
my ($header, $footer) = &cshlNew($title);
&process();

sub process {
  my $action;                   # what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ($action eq 'anatomySobaInput')           { &anatomySobaInput();      }
    elsif ($action eq 'Analyze List')          { &anatomySoba('textarea'); }
    elsif ($action eq 'Analyze File')          { &anatomySoba('file');     }
    else { &anatomySobaInput(); }				# no action, show dag by default
} # sub process


sub anatomySobaInput {
  &printHtmlHeader(); 
#   print qq(<h1>$datatypeLabel Enrichment Analysis <a href="http://wiki.wormbase.org/index.php/User_Guide/TEA" target="_blank">$infogif</a></h1>);
  print qq(<h1>Enrichment Analysis <a href="http://wiki.wormbase.org/index.php/User_Guide/TEA" target="_blank">$infogif</a></h1>);
  print qq(Enter a gene set to find annotated terms that are over-represented using TEA (Tissue), PEA (Phenotype) and GEA (GO).<br/><br/>);

#   print qq(Enter a gene set to find $datatypeLabel);
#   print qq(objects that are over-represented regarding gene annotation frequency.<br/><br/>);
  print qq(<form method="post" action="tea.cgi" enctype="multipart/form-data">);
  print qq(<input type="hidden" name="datatype" value="$datatype">);
  print qq(<table cellpadding="8"><tr><td>);
  print qq(Enter a list of <i>C. elegans</i> gene names in the box<br/>);
  print qq(<textarea name="genelist" placeholder="eat-4 ZK512.6 WBGene00001135" rows="20" cols="60" onkeyup="if(this.value != '') { document.getElementById('geneNamesFile').disabled = 'disabled'; document.getElementById('analyzeFileButton').disabled = 'disabled'; } else { document.getElementById('geneNamesFile').disabled = ''; document.getElementById('analyzeFileButton').disabled = ''; }"></textarea><br/>);
#   print qq(<input Type="checkbox" name="showProcessTimes" Value="showProcessTimes">Show Process Times<br/>\n);
#   print qq(<input Type="checkbox" name="convertGeneToId" Value="convertGeneToId">Convert Genes to IDs<br/>\n);	# don't need this anymore, will figure out whether it needs to convert based on whether any non-WBGene IDs are in the input
  print qq(<input type="submit" name="action" id="analyzeListButton" value="Analyze List"><br/>);
  print qq(q value threshold : <input type="input" name="qvalueThreshold" id="qvalueThreshold" value="0.1"><br/><br/><br/>);
  print qq(</td><td valign="top"><p>or</p><br/>\n);
  print qq(</td><td valign="top">);
  print qq(Upload a file with gene names<br/>);
  print qq(<input type="file" name="geneNamesFile" id="geneNamesFile"/><br/>);
  print qq(<input type="submit" name="action" id="analyzeFileButton" value="Analyze File"><br/>\n);

  print qq(</td></tr><tr><td>);
  print qq(Optionally upload a file with background genes; then do 'Analyze List' or 'Analyze File'<br/>);
  print qq(<input type="file" name="backgroundGenesFile" id="backgroundGenesFile"/><br/><br/><br/>);

  print qq(</td></tr><tr><td>);
  print qq(Citations:<br>David Angeles-Albores, Raymond Y. N. Lee, Juancarlos Chan and Paul W. Sternberg (2016), "Tissue enrichment analysis for C. elegans genomics", BMC Bioinformatics 17:366<br/>Angeles-Albores, D; Lee, RYN; Chan, J; Sternberg, PW (2018): Two new functions in the WormBase Enrichment Suite. Micropublication: biology. Dataset. <a href="https://doi.org/10.17912/W25Q2N">https://doi.org/10.17912/W25Q2N</a><br/><br/>);

  print qq(</td></tr></table>);
#  print qq(<span style="font-size: 10pt;">Enter a gene list consisting of any accepted C. elegans gene names separated by spaces, colons or tabs into the box. Alternatively, input a plain-text file of gene names separated by spaces, colons or tabs using the 'Choose file' button. Text files must be plain text (.txt).<br/>The program returns enriched tissues as assessed by a hypergeometric function, after FDR correction. A bar chart containing the top 15 enriched tissues, sorted by increasing q-value and by decreasing fold-change is automatically generated. Bar coloring is intended to improve readability, and color does not convey information.<br/></span>\n);
  print qq(</form>);
#   &printMessageFooter(); 		# raymond wanted to remove this 2016 04 14
  &printHtmlFooter(); 
} # sub anatomySobaInput

sub anatomySoba {
  my ($filesource) = @_;
  &printHtmlHeader(); 

  my @datatypes = qw( anatomy phenotype go );

  my %datatypeToLabel;
  $datatypeToLabel{'anatomy'}   = 'TEA';
  $datatypeToLabel{'phenotype'} = 'PEA';
  $datatypeToLabel{'go'}        = 'GEA';
  foreach my $datatype (@datatypes) { print qq(Click <a href="#$datatype">here</a> for $datatypeToLabel{$datatype} results.<br/>); }
  print qq(<br/><br/>);

  my $backgroundList = '';
  my $upload_bg_filehandle = $query->upload("backgroundGenesFile");
  while ( <$upload_bg_filehandle> ) { $backgroundList .= $_; }
#   print qq(BGL $backgroundList BGL<br>);

  my $genelist = '';
  if ($filesource eq 'textarea') {
      ($var, $genelist) = &getHtmlVar($query, 'genelist'); }
    elsif ($filesource eq 'file') {
      my $upload_filehandle = $query->upload("geneNamesFile");
      while ( <$upload_filehandle> ) { $genelist .= $_; }
    }
  if ($genelist =~ m/,/) { $genelist =~ s/,/ /g; }
  my (@names) = split/\s+/, $genelist;
  my $hasNonWBGene = 0;
  foreach (@names) { if ($_ !~ m/WBGene/i) { $hasNonWBGene++; } }
  my $convertGeneToId = 0;
  if ($hasNonWBGene) { $convertGeneToId++; }

#   if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Getting postgres gene name mappings"); print qq($message<br/>\n); }
  my %geneNameToId; my %geneIdToName;
  if ($convertGeneToId) {
#     my ($geneNameToIdHashref, $geneIdToNameHashref) = &populateGeneNamesFromPostgres();
    my ($geneNameToIdHashref, $geneIdToNameHashref) = &populateGeneNamesFromFlatfile();
    %geneNameToId        = %$geneNameToIdHashref;
    %geneIdToName        = %$geneIdToNameHashref; }


  foreach my $datatype (@datatypes) {
    my $datatypeLabel = 'Tissue';
    if ($datatype eq 'anatomy')        { $datatypeLabel = 'Tissue'; }
      elsif ($datatype eq 'phenotype') { $datatypeLabel = 'Phenotype'; }
      elsif ($datatype eq 'go')        { $datatypeLabel = 'Gene Ontology'; }
      elsif ($datatype eq 'go_component')        { $datatypeLabel = 'Gene Ontology - Cellular Component'; }
      elsif ($datatype eq 'go_function')        { $datatypeLabel = 'Gene Ontology - Molecular Function'; }
      elsif ($datatype eq 'go_process')        { $datatypeLabel = 'Gene Ontology - Biological Process'; }

  print qq(<h1><a name="$datatype"></a>$datatypeLabel Enrichment Analysis Results <a href="http://wiki.wormbase.org/index.php/User_Guide/TEA" target="_blank">$infogif</a></h1>);

#   ($var, $datatype)          = &getHtmlVar($query, 'datatype');
#   ($var, my $showProcessTimes)  = &getHtmlVar($query, 'showProcessTimes');
#   ($var, my $convertGeneToId)   = &getHtmlVar($query, 'convertGeneToId');	# don't need this anymore, will figure out whether it needs to convert based on whether any non-WBGene IDs are in the input
#   ($var, my $calculateLcaNodes) = &getHtmlVar($query, 'calculateLcaNodes');
#   my ($var, $download)    = &getHtmlVar($query, 'download');
#   unless ($datatype) { $datatype = 'anatomy'; }			# later will need to change based on different datatypes

#   if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Loading dictionary"); print qq($message<br/>\n); }

  ($var, my $qvalueThreshold)          = &getHtmlVar($query, 'qvalueThreshold');
  unless ($qvalueThreshold) {   $qvalueThreshold = 0.2; }
  if ($qvalueThreshold > 0.2) { $qvalueThreshold = 0.2; }

  my %dict;
  my $dictFile = '/home/raymond/local/src/git/dictionary_generator/' . $datatype . '_dict.csv';
  open (DICT, "<$dictFile") or die "Cannot open $dictFile : $!";
  while (my $line = <DICT>) {
    my (@stuff) = split/,/, $line;
    if ($stuff[0] =~ m/WBGene/) { $dict{$stuff[0]}++; }
  } # while (my $line = <DICT>)
  close (DICT) or die "Cannot close $dictFile : $!";

#   if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Getting altId mappings"); print qq($message<br/>\n); }

#   my %geneAnatomy; my %anatomyGene;

#   if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Processing user genes for validity"); print qq($message<br/>\n); }
  unless ($convertGeneToId) { foreach my $name (@names) { $geneNameToId{lc($name)} = $name; $geneIdToName{$name} = $name; } }
  my @invalidGene; my %nodataGene; my %goodGene; 
  foreach my $name (@names) {
    my ($lcname) = lc($name);
    my $wbgene = '';
    if ($geneNameToId{$lcname}) {
        $wbgene = $geneNameToId{$lcname}; 
        if ($dict{$wbgene}) { $goodGene{$wbgene}{$name}++; }
          else { $nodataGene{$wbgene}{$name}++; } }
      else { push @invalidGene, $name; }
  } # foreach my $name (@names)

  my %anatomyTerms;
  if (scalar (keys %goodGene) > 0) {
      my $outputHtml = '';
#       if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Processing hgf"); print qq($message<br/>\n); }
      my $time = time;
      my $tempfile     = '/tmp/hyperGeo/hyperGeo' . $time;
      my $tempOutFile  = '/tmp/hyperGeo/hyperGeo' . $time . '.txt';
      my $tempMeltFile = '/tmp/hyperGeo/hyperGeo' . $time . '.csv';
      my $tempBgFile   = '/tmp/hyperGeo/hyperGeo' . $time . '.background.csv';
#       my $tempOutUrl   = '../data/hyperGeo/hyperGeo' . $time . '.txt';	# changed data to not be in other parent directory
      my $tempOutUrl   = 'data/hyperGeo/hyperGeo' . $time . '.txt';
      my $tempMeltUrl  = 'data/hyperGeo/hyperGeo' . $time . '.csv';
      open (OUT, ">$tempOutFile") or die "Cannot open $tempOutFile : $!";
#       my $tempImageUrl = '../data/hyperGeo/hyperGeo' . $time . '.svg';	# changed data to not be in other parent directory
      my $tempImageUrl = 'data/hyperGeo/hyperGeo' . $time . '.svg';
      open (TMP, ">$tempfile") or die "Cannot open $tempfile : $!";
#       print TMP qq(gene,reads\n);
      foreach my $gene (sort keys %goodGene) { print TMP qq($gene\n); }
      close (TMP) or die "Cannot close $tempfile : $!";
      my $someVariable = $datatype; if ($someVariable eq 'anatomy') { $someVariable = 'tissue'; }
      my $hyperData = '';
      if ($backgroundList) {
          open (BG, ">$tempBgFile") or die "Cannot open $tempBgFile : $!";
          print BG $backgroundList;
          close (BG) or die "Cannot close $tempBgFile : $!";
#           print qq(/home/raymond/local/src/git/TissueEnrichmentAnalysis/bin/tea  -d /home/raymond/local/src/git/dictionary_generator/${datatype}_dict.csv  $tempfile "$tempfile" $someVariable -q $qvalueThreshold -p -s -m $tempMeltFile -b $tempBgFile);
          $hyperData = `/home/raymond/local/src/git/TissueEnrichmentAnalysis/bin/tea  -d /home/raymond/local/src/git/dictionary_generator/${datatype}_dict.csv  $tempfile "$tempfile" $someVariable -q $qvalueThreshold -p -s -m $tempMeltFile -b $tempBgFile`; }
        else {
#           print qq(/home/raymond/local/src/git/TissueEnrichmentAnalysis/bin/tea  -d /home/raymond/local/src/git/dictionary_generator/${datatype}_dict.csv  $tempfile "$tempfile" $someVariable -q $qvalueThreshold -p -s -m $tempMeltFile);
          $hyperData = `/home/raymond/local/src/git/TissueEnrichmentAnalysis/bin/tea  -d /home/raymond/local/src/git/dictionary_generator/${datatype}_dict.csv  $tempfile "$tempfile" $someVariable -q $qvalueThreshold -p -s -m $tempMeltFile`; }

#       `rm $tempfile`;
# print qq(HPD $hyperData HPD<br/>);
#       ($hyperData) = $hyperData =~ m/------------------------\n(.*?)------------------------/ms;
#       if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Processing hgf results to display"); print qq($message<br/>\n); }
      my (@hyperData) = split/\n/, $hyperData;
#       my $header = shift @hyperData;
#       my (@header) = split/,/, $header;
#       my $th = join"</th><th>", @header;
      if (scalar @hyperData > 0) {
#           print qq(<table><tr><th>$th</th></tr>\n);
          $outputHtml .= qq(<table border="1" style="border-spacing: 0;">);  
          my @analyzePairs; 
          foreach my $line (@hyperData) {
            next if ($line =~ m/Executing script/);
            if ($line) {
              my (@line) = split/\t/, $line;
              my $qvalue = pop @line;
              print OUT qq($line\n);
              $line =~ s|\t|</td><td>|g;
              if ($line =~ m/(WBbt:\d+)/) { 
                 my $wbbt = $1;
                 push @analyzePairs, qq($wbbt $qvalue);
                 my $url = 'http://www.wormbase.org/species/all/anatomy_term/' .$wbbt . '#013--10';
                 $line =~ s/$wbbt/<a href="$url" target="_blank">$wbbt<\/a>/; }
               elsif ($line =~ m/(GO:\d+)/) { 
                 my $go = $1;
                 push @analyzePairs, qq($go $qvalue);
                 my $url = 'http://www.wormbase.org/species/all/go_term/' .$go . '#013--10';
                 $line =~ s/$go/<a href="$url" target="_blank">$go<\/a>/; }
               elsif ($line =~ m/(WBPhenotype:\d+)/) { 
                 my $wbphenotype = $1;
                 push @analyzePairs, qq($wbphenotype $qvalue);
                 my $url = 'http://www.wormbase.org/species/all/phenotype/' .$wbphenotype . '#013--10';
                 $line =~ s/$wbphenotype/<a href="$url" target="_blank">$wbphenotype<\/a>/; }
              $outputHtml .= qq(<tr><td align="right">$line</td></tr>);
            }
          } # foreach my $line (@hyperData)
          $outputHtml .= qq(</table>);  
          if (scalar @analyzePairs > 0) {
            my $analyzePairsData = join"\n", @analyzePairs;
            my $objectsQvalue = join"%0D%0A", @analyzePairs;			# join with url escape linebreak
#             $outputHtml .= qq(<iframe src="https://wobr.caltech.edu/~azurebrd/cgi-bin/soba_multi.cgi?objectsQvalue=${objectsQvalue}&filterForLcaFlag=1&filterLongestFlag=1&showControlsFlag=0&action=Analyze+Pairs" width="1270px" height="1070px"></iframe>);
            $outputHtml .= qq(<iframe src="https://wobr.caltech.edu/~azurebrd/cgi-bin/soba.cgi?wormbaseHeader=false&objectsQvalue=${objectsQvalue}&filterForLcaFlag=1&filterLongestFlag=1&showControlsFlag=0&action=Analyze+Terms" width="1270px" height="1070px"></iframe>);
# form button to link to soba instead of embedding with iframe
#             $outputHtml .= qq(<form method="get" action="/~azurebrd/cgi-bin/soba_multi.cgi">);
#             $outputHtml .= qq(<textarea rows="8" cols="80" name="objectsQvalue" id="objectsQvalue">$analyzePairsData</textarea>);
#             $outputHtml .= qq(<input type="hidden" name="filterForLcaFlag" id="filterForLcaFlag" value="1">);
#             $outputHtml .= qq(<input type="hidden" name="filterLongestFlag" id="filterLongestFlag" value="1">);
#             $outputHtml .= qq(<input type="hidden" name="showControlsFlag" id="showControlsFlag" value="0">);
#             $outputHtml .= qq(<input type="submit" name="action" id="analyzePairsButton" value="Analyze Pairs"><br/><br/><br/>);
#             $outputHtml .= qq(</form>); 
          } # if (scalar @analyzePairs > 0)
        } # if (scalar @hyperData > 0)
        else { $outputHtml .= qq(No significantly enriched cell/tissue has been found.<br/>\n); }
      close (OUT) or die "Cannot close $tempOutFile : $!";
      $outputHtml .= qq(<br/><br/>Return up to 15 most significant $datatype terms.<br/>);
      $outputHtml .= qq(<img src="$tempImageUrl"><br/>\n);
#      $outputHtml .= qq(This bar chart automatically displays up to 15 enriched tissues sorted by q-value (lowest q-value on top) and secondarily by fold-change (higher fold change on top) in case of tied q-values. Colors are meant to improve readability and do not convey information.<br/>);
      $outputHtml .= qq(Drag graph to your desktop to save.<br/>);
      $outputHtml .= qq(Download results table <a href="$tempOutUrl" target="_blank">here</a>.<br/>);
      $outputHtml .= qq(Download observed gene table <a href="$tempMeltUrl" target="_blank">here</a>.<br/><br/>);
      if ($outputHtml =~ m/dataframe is empty/) { print qq(No significantly enriched terms have been found.<br/><br/>\n); }
        else { print $outputHtml; }
    }
    else { print qq(There are no genes with annotated data to generate results.<br/>\n); }
  print qq(<br/>);
#   if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Displaying gene sets"); print qq($message<br/>\n); }
  if (scalar @invalidGene > 0) {
    my $countInvalidGenes = scalar @invalidGene;
    print qq(Your list has $countInvalidGenes invalid WormBase genes :<br/>\n);
    print qq(<textarea rows="6" cols="80">);
    foreach my $gene (@invalidGene) { print qq($gene\n); } 
    print qq(</textarea><br/><br/>); }
  if (scalar(keys %nodataGene) > 0) {
    my $countNodataGenes = scalar(keys %nodataGene);
    print qq(Your list has $countNodataGenes valid WormBase genes that have no annotated data or are excluded from testing :<br/>\n);
    print qq(<textarea rows="6" cols="80">);
    foreach my $gene (sort keys %nodataGene) {
      my $names = join", ", sort keys %{ $nodataGene{$gene} };
#       print qq($gene - $geneIdToName{$gene}\n);
      print qq($gene - $names\n); } 
    print qq(</textarea><br/><br/>); }
  if (scalar(keys %goodGene) > 0) {
    my $countGoodGenes = scalar(keys %goodGene);
    print qq(Your list has $countGoodGenes valid WormBase genes included in statistical testing :<br/>\n);
    print qq(<textarea rows="6" cols="80">);
    foreach my $gene (sort keys %goodGene) { 
#       print qq($gene - $geneIdToName{$gene}\n);
      my $names = join", ", sort keys %{ $goodGene{$gene} };
      print qq($gene - $names\n); } 
    print qq(</textarea><br/><br/>); }
#   print qq(<a href="tea.cgi?datatype=$datatype">perform another query</a><br/><br/><br/>);
  print qq(<a href="tea.cgi">perform another query</a><br/><br/><br/>);

  }

#   &printMessageFooter(); 		# raymond wanted to remove this 2016 04 14
  &printHtmlFooter(); 
# http://131.215.12.204/~azurebrd/cgi-bin/amigo.cgi?genelist=WBGene00010209+WBGene00010212+WBGene00010295+WBGene00015814+WBGene11111111+WBGene00000012+WBGene00000013+WBGene00000002+ZK512.6%0D%0A&action=anatomySoba
# http://131.215.12.204/~azurebrd/cgi-bin/amigo.cgi?action=anatomySobaInput
# WBGene00010209 WBGene00010212 WBGene00010295 WBGene00015814 WBGene11111111 WBGene00000012 WBGene00000013 WBGene00000002 ZK512.6 qwera 2z3zt daf-2
} # sub anatomySoba


sub populateGeneNamesFromFlatfile {
  my %geneNameToId; my %geneIdToName;
  my $infile = '/home/azurebrd/cron/gin_names/gin_names.txt';
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) {
    chomp $line;
    my ($id, $name, $primary) = split/\t/, $line;
    if ($primary eq 'primary') { $geneIdToName{$id}     = $name; }
    my ($lcname)           = lc($name);
    $geneNameToId{$lcname} = $id; }
  close (IN) or die "Cannot close $infile : $!";
  return (\%geneNameToId, \%geneIdToName);
} # sub populateGeneNamesFromFlatfile


sub printMessageFooter { print qq(if you use this tool, please cite us. If you have ideas, requests or bug-issues, please contact <a href="mailto:dangeles\@caltech.edu">dangeles\@caltech.edu</a><br/>); }

# sub printHtmlFooter { print qq(</body></html>\n); }
sub printHtmlFooter { print $footer }

sub printHtmlHeader { 
  my $javascript = << "EndOfText";
<script src="http://code.jquery.com/jquery-1.9.1.js"></script>
<script type="text/javascript">
function toggleShowHide(element) {
    document.getElementById(element).style.display = (document.getElementById(element).style.display == "none") ? "" : "none";
    return false;
}
function togglePlusMinus(element) {
    document.getElementById(element).innerHTML = (document.getElementById(element).innerHTML == "&nbsp;+&nbsp;") ? "&nbsp;-&nbsp;" : "&nbsp;+&nbsp;";
    return false;
}
</script>
EndOfText
  print qq(Content-type: text/html\n\n$header $javascript<body>\n); 
}

sub getHtmlVar {                
  no strict 'refs';             
  my ($query, $var, $err) = @_; 
  unless ($query->param("$var")) {
    if ($err) { print "<FONT COLOR=blue>ERROR : No such variable : $var</FONT><BR>\n"; }
  } else { 
    my $oop = $query->param("$var");
    $$var = &untaint($oop);         
    return ($var, $$var);           
  } 
} # sub getHtmlVar

sub untaint {
  my $tainted = shift;
  my $untainted;
  if ($tainted eq "") {
    $untainted = "";
  } else { # if ($tainted eq "")
    $tainted =~ s/[^\w\-.,;:?\/\\@#\$\%\^&*\>\<(){}[\]+=!~|' \t\n\r\f\"€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•—˜™š›œžŸ¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþ]//g;
    if ($tainted =~ m/^([\w\-.,;:?\/\\@#\$\%&\^*\>\<(){}[\]+=!~|' \t\n\r\f\"€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•—˜™š›œžŸ¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþ]+)$/) {
      $untainted = $1;
    } else {
      die "Bad data Tainted in $tainted";
    }
  } # else # if ($tainted eq "")
  return $untainted;
} # sub untaint

sub cshlNew {
  my $title = shift;
  unless ($title) { $title = ''; }      # init title in case blank
#   my $page = get "http://tazendra.caltech.edu/~azurebrd/sanger/wormbaseheader/WB_header_footer.html";
  my $page = get "https://caltech-curation.textpressolab.com/files/pub/wormbaseheader/WB_header_footer.html";
#  $page =~ s/href="\//href="http:\/\/www.wormbase.org\//g;
#  $page =~ s/src="/src="http:\/\/www.wormbase.org/g;
  ($header, $footer) = $page =~ m/^(.*?)\s+DIVIDER\s+(.*?)$/s;  # 2006 11 20    # get this from tazendra's script result.
#   $header =~ s/WormBase - Home Page/$title/g;                 # 2015 05 07    # wormbase 2.0
#   $header =~ s/WS2../WS256/g; # Dictionary freeze for P/GEA paper review process
  $header =~ s/<title>.*?<\/title>/<title>$title<\/title>/g;
  $header =~ s|https://www.wormbase.org/static/css/main.min.css|https://caltech-curation.textpressolab.com/files/pub/wormbaseheader/wormbase.css|g;
  return ($header, $footer);
} # sub cshlNew

sub getInfoGif {
  my $infogif = <<"EndOfText";
<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   version="1.1"
   width="14"
   height="14.485189"
   id="svg2"
   inkscape:version="0.48.3.1 r9886"
   sodipodi:docname="info.svg">
  <sodipodi:namedview
     pagecolor="#ffffff"
     bordercolor="#666666"
     borderopacity="1"
     objecttolerance="10"
     gridtolerance="10"
     guidetolerance="10"
     inkscape:pageopacity="0"
     inkscape:pageshadow="2"
     inkscape:window-width="640"
     inkscape:window-height="480"
     id="namedview15"
     showgrid="false"
     fit-margin-top="0"
     fit-margin-left="0"
     fit-margin-right="0"
     fit-margin-bottom="0"
     inkscape:zoom="4.3491799"
     inkscape:cx="7.0000054"
     inkscape:cy="7.2369895"
     inkscape:window-x="1044"
     inkscape:window-y="285"
     inkscape:window-maximized="0"
     inkscape:current-layer="svg2" />
  <defs
     id="defs4">
    <linearGradient
       id="linearGradient3759">
      <stop
         id="stop3761"
         style="stop-color:#ffffff;stop-opacity:1"
         offset="0" />
    </linearGradient>
    <linearGradient
       x1="274.82114"
       y1="438.6864"
       x2="278.05551"
       y2="438.6864"
       id="linearGradient3771"
       xlink:href="#linearGradient3759"
       gradientUnits="userSpaceOnUse"
       gradientTransform="matrix(3.8755518,0,0,3.8755519,-1003.9342,516.823)" />
  </defs>
  <metadata
     id="metadata7">
    <rdf:RDF>
      <cc:Work
         rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title />
      </cc:Work>
    </rdf:RDF>
  </metadata>
  <g
     transform="translate(-271.74999,-421.19103)"
     id="layer1">
    <text
       x="268.57144"
       y="423.79074"
       id="text3773"
       xml:space="preserve"
       style="font-size:18px;font-style:normal;font-weight:normal;line-height:125%;letter-spacing:0px;word-spacing:0px;fill:#000000;fill-opacity:1;stroke:none;font-family:Sans"
       sodipodi:linespacing="125%"><tspan
         x="268.57144"
         y="423.79074"
         id="tspan3775" /></text>
    <g
       transform="matrix(0.26666667,0,0,0.26666667,204.41666,314.18466)"
       id="g2990">
      <path
         d="m 296.78571,452.18362 a 15.535714,16.25 0 1 1 -31.07142,0 15.535714,16.25 0 1 1 31.07142,0 z"
         transform="matrix(1.4560743,0,0,1.4470161,-130.7709,-225.88336)"
         id="path2989"
         style="fill:#0000ff;fill-opacity:1;stroke:#0000ff;stroke-width:5;stroke-miterlimit:5;stroke-opacity:1;stroke-dasharray:none;stroke-dashoffset:0"
         inkscape:connector-curvature="0" />
      <text
         x="272.42188"
         y="441.70511"
         id="text3777"
         xml:space="preserve"
         style="font-size:18px;font-style:normal;font-weight:normal;line-height:125%;letter-spacing:0px;word-spacing:0px;fill:#000000;fill-opacity:1;stroke:none;font-family:Sans"
         sodipodi:linespacing="125%"><tspan
           x="272.42188"
           y="441.70511"
           id="tspan3779"
           style="font-size:40px;font-style:italic;font-variant:normal;font-weight:bold;font-stretch:normal;text-align:start;line-height:125%;writing-mode:lr-tb;text-anchor:start;fill:#ffffff;fill-opacity:1;stroke:#ffffff;stroke-opacity:1;font-family:Times New Roman;-inkscape-font-specification:'Times New Roman, Bold Italic'">i</tspan></text>
    </g>
  </g>
</svg>
EndOfText
  return $infogif;
}
