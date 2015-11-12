
#ifndef _H_starter
#define _H_starter
/* 
 * Copyright (c) 2008-2012, Andy Bierman, All Rights Reserved.
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 *

*** Generated by yangdump 2.2-5

    Combined SIL header
    module starter
    revision 2013-03-13
    namespace http://csikor.tmit.bme.hu/netconf/unify/starter
    organization BME-TMIT

 */

#include <xmlstring.h>

#include "dlq.h"
#include "ncxtypes.h"
#include "op.h"
#include "status.h"
#include "val.h"

#ifdef __cplusplus
extern "C" {
#endif

#define y_starter_M_starter (const xmlChar *)"starter"
#define y_starter_R_starter (const xmlChar *)"2013-03-13"

#define y_starter_N_appName (const xmlChar *)"appName"
#define y_starter_N_appParams (const xmlChar *)"appParams"
#define y_starter_N_capabilities (const xmlChar *)"capabilities"
#define y_starter_N_clickDescription (const xmlChar *)"clickDescription"
#define y_starter_N_etc (const xmlChar *)"etc"
#define y_starter_N_load (const xmlChar *)"load"
#define y_starter_N_loadFifteen (const xmlChar *)"loadFifteen"
#define y_starter_N_loadFive (const xmlChar *)"loadFive"
#define y_starter_N_loadOne (const xmlChar *)"loadOne"
#define y_starter_N_pid (const xmlChar *)"pid"
#define y_starter_N_port (const xmlChar *)"port"
#define y_starter_N_processData (const xmlChar *)"processData"
#define y_starter_N_processDone (const xmlChar *)"processDone"
#define y_starter_N_processID (const xmlChar *)"processID"
#define y_starter_N_processName (const xmlChar *)"processName"
#define y_starter_N_processStatus (const xmlChar *)"processStatus"
#define y_starter_N_processes (const xmlChar *)"processes"
#define y_starter_N_processesCurrentlyExists (const xmlChar *)"processesCurrentlyExists"
#define y_starter_N_starter (const xmlChar *)"starter"
#define y_starter_N_starter_get_load (const xmlChar *)"starter_get-load"
#define y_starter_N_starter_get_processes (const xmlChar *)"starter_get-processes"
#define y_starter_N_starter_kill_vnf (const xmlChar *)"starter_kill-vnf"
#define y_starter_N_starter_start_vnf (const xmlChar *)"starter_start-vnf"
#define y_starter_N_success (const xmlChar *)"success"
#define y_starter_N_vnfID (const xmlChar *)"vnfID"

/* leaf-list /starter/capabilities */
typedef struct y_starter_T_starter_capabilities_ {
    dlq_hdr_t qhdr;
    xmlChar *capabilities;
} y_starter_T_starter_capabilities;

/* container /starter */
typedef struct y_starter_T_starter_ {
    xmlChar *appName;
    xmlChar *appParams;
    dlq_hdr_t capabilities;
} y_starter_T_starter;

/* container /starter_start-vnf/input */
typedef struct y_starter_T_starter_start_vnf_input_ {
    xmlChar *port;
    xmlChar *clickDescription;
} y_starter_T_starter_start_vnf_input;

/* container /starter_start-vnf/output */
typedef struct y_starter_T_starter_start_vnf_output_ {
    xmlChar *vnfID;
} y_starter_T_starter_start_vnf_output;

/* rpc /starter_start-vnf */
typedef struct y_starter_T_starter_start_vnf_ {
    y_starter_T_starter_start_vnf_input input;
    y_starter_T_starter_start_vnf_output output;
} y_starter_T_starter_start_vnf;

/* container /starter_kill-vnf/input */
typedef struct y_starter_T_starter_kill_vnf_input_ {
    xmlChar *vnfID;
} y_starter_T_starter_kill_vnf_input;

/* container /starter_kill-vnf/output */
typedef struct y_starter_T_starter_kill_vnf_output_ {
    xmlChar *success;
} y_starter_T_starter_kill_vnf_output;

/* rpc /starter_kill-vnf */
typedef struct y_starter_T_starter_kill_vnf_ {
    y_starter_T_starter_kill_vnf_input input;
    y_starter_T_starter_kill_vnf_output output;
} y_starter_T_starter_kill_vnf;

/* list /starter_get-load/output/load */
typedef struct y_starter_T_starter_get_load_output_load_ {
    dlq_hdr_t qhdr;
    xmlChar *loadOne;
    xmlChar *loadFive;
    xmlChar *loadFifteen;
    xmlChar *processesCurrentlyExists;
    xmlChar *pid;
} y_starter_T_starter_get_load_output_load;

/* container /starter_get-load/output */
typedef struct y_starter_T_starter_get_load_output_ {
    dlq_hdr_t load;
} y_starter_T_starter_get_load_output;

/* container /starter_get-load/input */
typedef struct y_starter_T_starter_get_load_input_ {
} y_starter_T_starter_get_load_input;

/* rpc /starter_get-load */
typedef struct y_starter_T_starter_get_load_ {
    y_starter_T_starter_get_load_output output;
    y_starter_T_starter_get_load_input input;
} y_starter_T_starter_get_load;

/* container /starter_get-processes/output */
typedef struct y_starter_T_starter_get_processes_output_ {
    xmlChar *processes;
} y_starter_T_starter_get_processes_output;

/* container /starter_get-processes/input */
typedef struct y_starter_T_starter_get_processes_input_ {
} y_starter_T_starter_get_processes_input;

/* rpc /starter_get-processes */
typedef struct y_starter_T_starter_get_processes_ {
    y_starter_T_starter_get_processes_output output;
    y_starter_T_starter_get_processes_input input;
} y_starter_T_starter_get_processes;

/* notification /processData */
typedef struct y_starter_T_processData_ {
    xmlChar *processName;
    int32 processID;
} y_starter_T_processData;

/* notification /processDone */
typedef struct y_starter_T_processDone_ {
    xmlChar *processStatus;
    xmlChar *etc;
} y_starter_T_processDone;

/********************************************************************
* FUNCTION y_starter_processData_send
* 
* Send a y_starter_processData notification
* Called by your code when notification event occurs
* 
********************************************************************/
extern void y_starter_processData_send (
    const xmlChar *processName,
    int32 processID);


/********************************************************************
* FUNCTION y_starter_processDone_send
* 
* Send a y_starter_processDone notification
* Called by your code when notification event occurs
* 
********************************************************************/
extern void y_starter_processDone_send (
    const xmlChar *processStatus,
    const xmlChar *etc);

/********************************************************************
* FUNCTION y_starter_init
* 
* initialize the starter server instrumentation library
* 
* INPUTS:
*    modname == requested module name
*    revision == requested version (NULL for any)
* 
* RETURNS:
*     error status
********************************************************************/
extern status_t y_starter_init (
    const xmlChar *modname,
    const xmlChar *revision);

/********************************************************************
* FUNCTION y_starter_init2
* 
* SIL init phase 2: non-config data structures
* Called after running config is loaded
* 
* RETURNS:
*     error status
********************************************************************/
extern status_t y_starter_init2 (void);

/********************************************************************
* FUNCTION y_starter_cleanup
*    cleanup the server instrumentation library
* 
********************************************************************/
extern void y_starter_cleanup (void);

#ifdef __cplusplus
} /* end extern 'C' */
#endif

#endif