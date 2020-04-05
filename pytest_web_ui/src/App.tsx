import React from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import {
  HashRouter as Router,
  Route,
  useLocation,
} from "react-router-dom";
import { StyleSheet, css } from "aphrodite";
import _ from "lodash";

import { COLWIDTH, BranchNode } from "./Common";
import { NavColumn } from "./NavColumn";
import { NavBreadcrumbs, InfoPane } from "./CentrePane";

/**
 * Top level App component.
 */
const App = () => {
  return (
    <Router>
      <Route path="/"
        render={
          ({ location }) => {
            return <TestRunner url={location.pathname} />;
          }
        }
      />
    </Router>
  );
};

interface TestRunnerProps {
  url: string,
}

interface TestRunnerState {
  resultTree: BranchNode | null,
  loading: boolean,
  socket: SocketIOClient.Socket | null,
}

class TestRunner extends React.Component<TestRunnerProps, TestRunnerState> {
  constructor(props: TestRunnerProps) {
    super(props);
    this.state = {
      resultTree: null,
      loading: false,
      socket: null,
    }
    this.handleUpdate = this.handleUpdate.bind(this);
    this.handleTestRun = this.handleTestRun.bind(this);
  }

  /**
   * When the component mounts, we initiate the websocket connection and
   * make an API call to get the result tree.
   */
  componentDidMount() {
    console.log("INIT WEBSOCKET");
    const socket = io();
    this.setState({ loading: true, socket: socket }, () => {
      socket.on('update', this.handleUpdate);
      this.getResultTree();
    });
  }

  /**
   * Make an API call to get the result tree data. Called at start of day when
   * this component mounts, then further updates are handled by the websocket
   * connection.
   */
  getResultTree() {
    axios.get("/api/v1/result-tree").then(response => {
      this.setState({ resultTree: response.data, loading: false });
    });
  }

  /**
   * Handle an update event received over a websocket.
   * @param data Update data received over socket
   */
  handleUpdate(data: BranchNode) {
    console.log("Handling websocket update");
    console.log(data);

    const root = this.state.resultTree;
    if (!root) {
      return;
    }

    this.setState((state) => {
      const newTree = updateResultTree(root, data);
      return { resultTree: newTree };
    });
  }

  /**
   * Run a test after its run button has been clicked.
   * @param nodeid ID of node to run
   */
  handleTestRun(nodeid: string) {
    if (!this.state.socket) {
      console.log("Socket connection not yet established");
      return;
    }
    this.state.socket.emit("run test", nodeid);
  }

  /**
   * Render the test runner UI. Currently this component acts as the stateful
   * store and hands off rendering logic to a separate stateless component.
   */
  render() {
    const selection = parseSelection(this.props.url);
    const selectedBranch = getSelectedBranch(
      selection,
      this.state.resultTree,
    );

    return (
      <TestRunnerDisplay
        selectedBranch={selectedBranch}
        selection={selection}
        handleTestRun={this.handleTestRun}
      />
    );
  }
}

/**
 * Parse the current URL path (excluding query parameters) and return the
 * nodeids of the currently selected branches.
 * @param url URL path string
 */
const parseSelection = (url: string): Array<string> => {
  const trimmedPath = url.replace(/^\/+|\/+$/g, '');
  if (trimmedPath.length === 0) {
    return [];
  }
  const pathElements = trimmedPath.split("/");
  return pathElements.map(decodeURIComponent);
};

/**
 * Update a particular node in the result tree with new data.
 * @param currNode Existing in result tree to update
 * @param parentNodeIds List of parent node IDs to reach node to update
 * @param updateData Update data for new node
 */
const updateResultTree = (
  currRoot: BranchNode, updateData: BranchNode
): BranchNode => {
  const newRoot = { ...currRoot };
  _.merge(newRoot, updateData);
  return newRoot;
};

interface TestRunnerDisplayProps {
  selectedBranch: BranchNode | null,
  selection: Array<string>,
  handleTestRun: (nodeid: string) => void,
}

/**
 * Render the navigation column, top breadcrumb menu and the central information
 * pane together.
 * @param props render properties
 */
const TestRunnerDisplay = (props: TestRunnerDisplayProps) => {
  const query = useQuery();
  const selectedLeafID = query.get("selectedLeaf");
  const selectedLeaf = (selectedLeafID && props.selectedBranch) ?
    props.selectedBranch.child_leaves[selectedLeafID] : null;

  return (
    <div>
      <NavColumn
        selectedBranch={props.selectedBranch}
        selectedLeafID={selectedLeafID}
        selection={props.selection}
        handleTestRun={props.handleTestRun}
      />
      <div className={css(styles.centrePane)}>
        <NavBreadcrumbs selection={props.selection} />
        <InfoPane selectedLeaf={selectedLeaf} />
      </div>
    </div>
  );
};

/**
 * Modified react hook to parse the current query parameters in the URL. These
 * are expected in the form "?x=y".
 */
const useQuery = () => new URLSearchParams(useLocation().search);

/**
 * Get the currently selected branch node, or null if the result tree is not yet
 * loaded.
 * @param state App state
 */
const getSelectedBranch = (
  selection: Array<string>, resultTree: BranchNode | null
) => {
  if (resultTree) {
    const selectedBranch = selection.reduce(
      (node: BranchNode | undefined, selection: string) => (
        node?.child_branches[selection]
      ),
      resultTree,
    );
    if (selectedBranch) {
      return selectedBranch;
    } else {
      console.log(selection);
      return null;
    }
  } else {
    return null;
  }
};

const styles = StyleSheet.create({
  centrePane: {
    "margin-left": COLWIDTH,
    padding: "10px 10px",
  },
});

export default App;
