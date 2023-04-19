<?php

$url="https://www.sonofind.com/api/v2/";
$user="abc@abc.com";
$pw="demo";

$trackcode="SCD072005";
if($_GET['trackcode']) {
    $trackcode=$_GET['trackcode'];
}

echo "<pre>";

$oTest=new SONOfindAPI($url);
$oTest->openSession();
$oTest->authenticate($user,$pw);

#$oTest->getLabels();
#$oTest->getCD('SCD');
#$oTest->getTrack($trackcode);
$oTest->downloadTrack($trackcode);
#$ret = $oTest->ackTrack($trackcode);
#$ret = $oTest->newTracks();

/**
 * PHP class using CURL module
 * 
 * @author michael ettl
 *
 */
class SONOfindAPI {
    
    protected $baseurl;
    protected $ch;
    protected $mode="GET";
    protected $response;
    /**
     * 
     * @var SimpleXMLElement
     */
    protected $xml;
    protected $sid='';
    
    public function __construct($url="") {
        $this->baseurl=$url;
    }
    
    /**
     * query server
     * @param array $aParams - POST parameters
     * @param array $aGetParams - optional GET parameters
     * @return SimpleXMLElement
     */
    private function startCurl($aParams,$aGetParams=array()) {
        $this->initCurl($aParams,$aGetParams);
        return($this->executeCurl());
    }
    
    /**
     * 
     * @param array $aParams - POST parameters
     * @param array $aGetParams - optional GET parameters
     */
    private function initCurl($aParams,$aGetParams=array()) {
        #echo "SID".$this->sid;
        #if($this->sid) {
        #    $aParams['sid']=$this->sid;
        #}
        if($this->mode=='GET') {
            $url = $this->baseurl.implode("/",$aParams);
            if(count($aGetParams)>0) {
                $url .= "?".http_build_query($aGetParams);
            }
        } else {
            $url = $this->baseurl;
        }
        $this->debug("Request: $url");
        
        $this->ch = curl_init($url);
        curl_setopt($this->ch, CURLOPT_RETURNTRANSFER, true);
        
        // set authentication header
        if($this->sid) {
            curl_setopt($this->ch, CURLOPT_HTTPHEADER, array(
                'SFAPIV2-SID: '.$this->sid
            ));
        }
        
        if($this->mode!='GET') {
            curl_setopt($this->ch, CURLOPT_POST, true);
            curl_setopt($this->ch, CURLOPT_CUSTOMREQUEST, "POST");
            curl_setopt(
                $this->ch,
                CURLOPT_POSTFIELDS,
                $aParams
                );
        }
    }
    
    /**
     * execute CURL query created by initCurl
     * @throws Exception
     * @return SimpleXMLElement
     */
    private function executeCurl() {
        $this->response = curl_exec($this->ch);
        #echo $this->response;
        if(! $this->response) {
            throw new Exception("CURL Connection Error:".curl_error($this->ch)."\n",1011);
        }
        curl_close($this->ch);
        $this->debug( "RESPONSE: ".$this->response);
        $this->xml = new SimpleXMLElement($this->response);
        $result = $this->xml;
        #$this->debug( "RESULT: ".$result->ax_success);
        if($result->ax_success==-1) {
            $error = $result->ax_msg;
            $errormsg = $result->ax_errmsg;
            $errcode = (string) $result->ax_errcode;
            #ax_addstatus
            throw new Exception("XML Error on $url\n\n".$result->ax_msg."\n",$errcode);
        }
        if((string) $this->xml->ax_msg[0])
            $this->debug( "Response: ".$this->xml->ax_msg[0]);
            return($this->xml);
    }
    
    private function debug($msg) {
        echo $msg."\n";
    }
    
    /**
     * initiate session with sonoton server
     */
    public function openSession() {
        $this->startCurl(array('ac'=>'opensession'));
        $result = $this->xml->xpath('/mmd/sid');
        $this->sid=(string) $result[0];
        $this->debug( "SESSION-ID: ".$this->sid);
    }
    
    /**
     * authenticate with sonoton server
     * 
     * @param string $user
     * @param string $pass
     */
    public function authenticate($user='',$pass='') {
        $aParams['ac']='auth';
        $aParams['user']=$user;
        $aParams['pass']=md5($pass."~".$this->sid);
        $this->startCurl($aParams);
        #$this->debug( $this->response);
        #$result = $this->xml->xpath('/mmd/sid');
    }
    
    /**
     * 
     * @param string $trackcode
     * @return objct
     */
    
    
    /**
     * 
     * @param unknown $trackcode
     * @return unknown
     */
    public function getTrack($trackcode) {
        $aParams['ac']='mmd';
        $aParams['trackcode']=$trackcode;
        $this->startCurl($aParams);
        $xPath="/mmd/track";
        $this->debug(print_r($this->xml,true));
        $XMLtrack=$this->xml->track[0];
        echo "Track found: ".$XMLtrack->trackcode[0];
        echo "Track deactivated: ".$XMLtrack->deactivated[0]."\n";
        return($XMLtrack);
    }
    
    /**
     * fetch labels available for download
     * @return string[]
     */
    public function getLabels() {
        $aParams['ac']='labels';
        $resp=$this->startCurl($aParams);
        $this->debug( "Labels found: ".$this->xml->cnt);
        $xPath="/mmd/labelinfo/label";
        $XMLfiles = $this->xml->xpath($xPath);
        $aLabels=array();
        foreach ($XMLfiles as $files) {
            $aLabels[] = (string) $files[0];
        }
        #print_r($aLabels);
        return($aLabels);
    }
    
    /**
     * fetch list of albums available for this label
     * @param string $label
     * @return string[]
     */
    public function getCD($label) {
        $aParams['ac']='cds';
        $aParams['label']=$label;
        $resp=$this->startCurl($aParams);
        $this->debug( "Albums found: ".$this->xml->cnt);
        #print_r($this->xml);
        $xPath="/mmd/cd/cdcode";
        $XMLfiles = $this->xml->xpath($xPath);
        $aAlbumcode=array();
        foreach ($XMLfiles as $files) {
            $aAlbumcode[] = (string) $files[0];
        }
        #print_r($aAlbumcode);
        return($aAlbumcode);
    }
    
    /**
     * acknowledge receipt of track
     * @param string $trackcode
     * @return SimpleXMLElement
     */
    public function ackTrack($trackcode) {
        $aParams['ac']='ack';
        $aParams['trackcode']=$trackcode;
        $resp=$this->startCurl($aParams);
        return($resp);
    }
    
    /**
     * 
     * Fetch newTracks
     * @param string $label
     * @return SimpleXMLElement
     */
    public function newTracks($label="") {
        $aParams['ac']='newtracks';
    	if($label) {
    		$aParams[]=$label;
    	}
        $aGetParams['limit']=1000;
        $aGetParams['skipstems']=1;
        $resp=$this->startCurl($aParams,$aGetParams);
        $trackcodes= (array) $XMLtrack=$this->xml->trackcodes;
        #echo "List of new tracks: ".print_r($trackcodes,true)."\n";
        return($resp);
    }
    
    /**
     * Download audio for track
     * @param string $trackcode
     * @throws Exception
     */
    public function downloadTrack($trackcode) {
        $this->getTrack($trackcode);
        $xPath="/mmd/track[@trackcode='$trackcode']/files/file[@content='audio']";
        #[@quality='320']";
        $XMLfiles = $this->xml->xpath($xPath);
        #print_r($XMLfiles);
        
        foreach ($XMLfiles as $files) {
            #print_r($files);
            $downurl=(string) $files[0];
            $this->debug( "DOWNLOADURL: $downurl");
            #$downparam=parse_url($downurl, PHP_URL_QUERY);
            #echo "URL:$downparam\n";
            #parse_str($downparam,$aParams);
            try {
                $this->initCurl(array());
                curl_setopt($this->ch, CURLOPT_URL, $downurl);
                $this->executeCurl();
                $downloadURL = (string) $this->xml->url[0];
                echo sprintf("DOWNLOADURL %s %s: <a href='%s'>%s</a>\n",$files[0]['type'],$files[0]['quality'],$downloadURL,$downloadURL);
            } catch (Exception $e) {
                if($e->getCode()==670) {
                    echo "GOT ERROR 670 - missing DOWNLOAD FILE for ".$files[0]['quality']."\n";                    
                } else {
                    throw $e;
                }
            }
        }
    }
    
}
