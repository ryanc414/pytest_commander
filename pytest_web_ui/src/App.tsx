import React from 'react';
import axios from 'axios';
import {
  ListGroup, ListGroupItem, Breadcrumb, BreadcrumbItem
} from 'reactstrap';
import Sidebar from 'react-sidebar';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome } from '@fortawesome/free-solid-svg-icons';

interface BranchNode {
  nodeid: string,
  status: string,
  parent_nodeids: Array<string>,
  child_branches: { [key: string]: BranchNode },
  child_leaves: { [key: string]: LeafNode },
}

interface LeafNode {
  nodeid: string,
  status: string,
  parent_nodeids: Array<string>,
  longrepr: string,
}

interface AppState {
  resultTree: BranchNode | null,
  loading: boolean,
  sidebarOpen: boolean,
  selectedBranches: Array<string>,
  selectedLeaf: string | null,
}

/**
 * Top level App component.
 */
class App extends React.Component<object, AppState> {
  constructor(props: object) {
    super(props);
    this.state = {
      resultTree: null,
      loading: false,
      sidebarOpen: true,
      selectedBranches: [],
      selectedLeaf: null,
    }
    this.onSetSidebarOpen = this.onSetSidebarOpen.bind(this);
    this.handleBranchClick = this.handleBranchClick.bind(this);
    this.handleLeafClick = this.handleLeafClick.bind(this);
    this.handleBreadcrumbClick = this.handleBreadcrumbClick.bind(this);
  }

  componentDidMount() {
    this.setState({ loading: true }, this.getResultTree);
  }

  getResultTree() {
    axios.get("/api/v1/result-tree").then(response => {
      this.setState({ resultTree: response.data, loading: false });
    });
  }

  onSetSidebarOpen(open: boolean) {
    this.setState({ sidebarOpen: open })
  }

  /**
   * Handle a branch node being clicked.
   * @param nodeid ID of clicked branch node
   */
  handleBranchClick(nodeid: string) {
    this.setState((state) => ({
      selectedBranches: state.selectedBranches.concat([nodeid]),
      selectedLeaf: null,
    }));
  }

  /**
   * Handle a leaf node being clicked.
   * @param nodeid ID of clicked leaf node
   */
  handleLeafClick(nodeid: string) {
    this.setState((state) => ({
      selectedLeaf: nodeid,
    }))
  }

  handleBreadcrumbClick(nodeid: string, index: number) {
    this.setState((state: AppState) => {
      // An index of -1 is used to indicate the home icon was clicked.
      if (index < 0) {
        return { selectedBranches: [] };
      }

      if (state.selectedBranches[index] !== nodeid) {
        console.log(
          "Breadcrumb entry " + nodeid + " not in current selection."
        );
        return null;
      }

      return {
        selectedBranches: state.selectedBranches.slice(0, index + 1)
      };
    });
  }

  render() {
    const selectedBranch = getSelectedBranch(this.state);

    const selectedLeaf = selectedBranch && this.state.selectedLeaf ?
      selectedBranch.child_leaves[this.state.selectedLeaf] : null;

    return (
      <Sidebar
        sidebar={
          < NavColumn
            selectedBranch={selectedBranch}
            handleBranchClick={this.handleBranchClick}
            handleLeafClick={this.handleLeafClick}
          />
        }
        open={this.state.sidebarOpen}
        docked={true}
        onSetOpen={this.onSetSidebarOpen}
        styles={{ sidebar: { background: "white" } }}
      >
        <NavBreadcrumbs
          selectedBranches={this.state.selectedBranches}
          handleBreadcrumbClick={this.handleBreadcrumbClick}
        />
        <InfoPane selectedLeaf={selectedLeaf} />
      </Sidebar >
    );
  }
}

/**
 * Get the currently selected branch node, or null if the result tree is not yet loaded.
 * @param state App state
 */
const getSelectedBranch = (state: AppState) => {
  if (state.resultTree) {
    return state.selectedBranches.reduce(
      (node: BranchNode, selection: string) => node.child_branches[selection],
      state.resultTree,
    );
  } else {
    return null;
  }
};

interface NavProps {
  selectedBranch: BranchNode | null,
  handleBranchClick: (nodeid: string) => void,
  handleLeafClick: (nodeid: string) => void,
}

interface InfoPaneProps {
  selectedLeaf: LeafNode | null,
}

/**
 * NavColumn component: renders the current navigation selection.
 * @param props Component props
 */
const NavColumn = (props: NavProps) => {
  if (!props.selectedBranch) {
    return <span>Loading...</span>;
  }

  const childBranches = Object.keys(props.selectedBranch.child_branches);
  const childLeaves = Object.keys(props.selectedBranch.child_leaves);
  return (
    <ListGroup>
      {
        childBranches.map(
          (entry: string) => (
            <ListGroupItem onClick={() => props.handleBranchClick(entry)}>
              {entry + " (branch)"}
            </ListGroupItem>
          )
        )
      }
      {
        childLeaves.map(
          (entry: string) => (
            <ListGroupItem onClick={() => props.handleLeafClick(entry)}>
              {entry + " (leaf)"}
            </ListGroupItem>
          )
        )
      }
    </ListGroup>
  );
}

/**
 * InfoPane component: renders information on the currently selected testcase (if any)
 * @param props Component props
 */
const InfoPane = (props: InfoPaneProps) => {
  const selectedNodeid = props.selectedLeaf ? props.selectedLeaf.nodeid : null;
  return <span>{selectedNodeid}</span>;
}

interface NavBreadcrumbsProps {
  selectedBranches: Array<string>,
  handleBreadcrumbClick: (nodeid: string, index: number) => void,
}

const NavBreadcrumbs = (props: NavBreadcrumbsProps) => {
  const numSelected = props.selectedBranches.length;

  if (!numSelected) {
    return (
      <Breadcrumb>
        <BreadcrumbItem><FontAwesomeIcon icon={faHome} /></BreadcrumbItem>
      </Breadcrumb>
    );
  }

  const currSelected = props.selectedBranches[numSelected - 1];
  const restSelected = props.selectedBranches.slice(0, numSelected - 1);

  return (
    <Breadcrumb>
      <BreadcrumbItem>
        <FontAwesomeIcon
          icon={faHome}
          onClick={() => props.handleBreadcrumbClick("", -1)}
        />
      </BreadcrumbItem>
      {
        restSelected.map(
          (nodeid: string, index: number) => (
            <BreadcrumbItem>
              <button onClick={() => props.handleBreadcrumbClick(nodeid, index)}>
                {nodeid}
              </button>
            </BreadcrumbItem>
          )
        )
      }
      <BreadcrumbItem>{currSelected}</BreadcrumbItem>
    </Breadcrumb>
  );
};

export default App;
